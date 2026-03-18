"""Sensor Agent — maintains rolling Tension Score per relationship and fires TensionAlerts."""
import uuid
import json
import logging
from datetime import datetime
from typing import Optional
import google.generativeai as genai
from app.config import settings
from app.kafka.producer import SynapseProducer
from app.kafka.topics import TOPICS

logger = logging.getLogger(__name__)

# EMA smoothing factor
ALPHA = 0.3

# Redis key templates
TENSION_SCORE_KEY   = "tension:{relationship_id}"
TENSION_COUNT_KEY   = "tension_count:{relationship_id}"
RATE_LIMIT_KEY      = "alert_rate:{relationship_id}"
RATE_LIMIT_TTL_S    = 6 * 3600  # 6 hours


class TensionAlert:
    """Typed wrapper for the TensionAlert payload emitted to Kafka."""
    def __init__(
        self,
        relationship_id: str,
        party_ids: list[str],
        tension_score: float,
        tension_type: str,
        triggering_events: list[str],
        context_summary: str,
        recommended_negotiation_type: str,
    ):
        self.alert_id = str(uuid.uuid4())
        self.relationship_id = relationship_id
        self.party_ids = party_ids
        self.tension_score = tension_score
        self.tension_type = tension_type
        self.triggering_events = triggering_events
        self.context_summary = context_summary
        self.recommended_negotiation_type = recommended_negotiation_type
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return self.__dict__


class SensorAgent:
    """
    Consumes CanonicalEvent payloads from Kafka tension signals topic,
    maintains per-relationship EMA tension scores in Redis,
    and emits TensionAlerts when the threshold is breached for ≥2 consecutive events.
    """

    def __init__(self, redis_client, kafka_producer: SynapseProducer, tension_threshold: int = 65):
        self.redis = redis_client
        self.producer = kafka_producer
        self.threshold = tension_threshold / 100.0  # normalize to 0–1

        # Configure Gemini for ambiguous-range scoring
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._gemini = genai.GenerativeModel(
            settings.GEMINI_FLASH_MODEL,
            generation_config=genai.GenerationConfig(temperature=0.1, top_p=0.95),
        )

    # ── Tension score management ──────────────────────────────────────────────

    async def _get_tension_score(self, relationship_id: str) -> float:
        raw = await self.redis.get(TENSION_SCORE_KEY.format(relationship_id=relationship_id))
        return float(raw) if raw else 0.30  # default neutral baseline

    async def _set_tension_score(self, relationship_id: str, score: float):
        await self.redis.setex(
            TENSION_SCORE_KEY.format(relationship_id=relationship_id),
            86400,  # 24h TTL
            str(score),
        )

    async def _get_breach_count(self, relationship_id: str) -> int:
        raw = await self.redis.get(TENSION_COUNT_KEY.format(relationship_id=relationship_id))
        return int(raw) if raw else 0

    async def _set_breach_count(self, relationship_id: str, count: int):
        await self.redis.setex(
            TENSION_COUNT_KEY.format(relationship_id=relationship_id),
            86400,
            str(count),
        )

    async def _is_rate_limited(self, relationship_id: str) -> bool:
        key = RATE_LIMIT_KEY.format(relationship_id=relationship_id)
        return await self.redis.exists(key) == 1

    async def _set_rate_limit(self, relationship_id: str):
        key = RATE_LIMIT_KEY.format(relationship_id=relationship_id)
        await self.redis.setex(key, RATE_LIMIT_TTL_S, "1")

    # ── Gemini for ambiguous cases ────────────────────────────────────────────

    async def compute_tension_with_gemini(self, event_payload: dict, context: str) -> float:
        """
        Call Gemini 2.0 Flash with function calling for ambiguous-range events (0.45–0.65).
        Returns a refined float score.
        """
        score_tool = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name="report_tension_score",
                    description="Report the computed tension score for this event.",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            "score": genai.protos.Schema(
                                type=genai.protos.Type.NUMBER,
                                description="Tension score 0.0–1.0",
                            ),
                            "reasoning": genai.protos.Schema(
                                type=genai.protos.Type.STRING,
                                description="One-sentence rationale",
                            ),
                        },
                        required=["score", "reasoning"],
                    ),
                )
            ]
        )

        prompt = (
            f"You are a relationship tension analyzer. Evaluate this event and return a tension score.\n"
            f"Event metadata: {json.dumps(event_payload, default=str)}\n"
            f"Relationship context: {context}\n"
            f"Return a score between 0.0 (no tension) and 1.0 (critical tension). Be conservative."
        )

        try:
            response = self._gemini.generate_content([prompt], tools=[score_tool])
            for part in response.candidates[0].content.parts:
                if part.function_call and part.function_call.name == "report_tension_score":
                    return float(part.function_call.args.get("score", 0.5))
        except Exception as e:
            logger.warning(f"Gemini tension call failed: {e}")

        return 0.5  # safe fallback

    # ── Main processing entry point ───────────────────────────────────────────

    async def process_event(self, event_payload: dict) -> Optional[TensionAlert]:
        """
        Process a single tension signal event.
        Apply EMA, anti-noise filter, and emit alert if threshold breached.
        """
        relationship_id = event_payload.get("relationship_id")
        if not relationship_id:
            logger.warning("Event missing relationship_id — skipping.")
            return None

        raw_score = float(event_payload.get("pre_tension_score", 0.30))
        party_ids = event_payload.get("party_ids", [])
        context_tags = event_payload.get("context_tags", [])
        event_id = event_payload.get("event_id", "unknown")

        # Gemini refinement for ambiguous-range scores
        if 0.45 <= raw_score <= 0.65:
            raw_score = await self.compute_tension_with_gemini(event_payload, "")

        # EMA update
        old_score = await self._get_tension_score(relationship_id)
        new_score = ALPHA * raw_score + (1 - ALPHA) * old_score
        await self._set_tension_score(relationship_id, new_score)

        # Anti-noise: count consecutive breaches
        breach_count = await self._get_breach_count(relationship_id)
        if new_score >= self.threshold:
            breach_count += 1
        else:
            breach_count = 0
        await self._set_breach_count(relationship_id, breach_count)

        # Fire alert only after 2 consecutive breaches AND not rate-limited
        if breach_count >= 2 and not await self._is_rate_limited(relationship_id):
            tension_type = self._classify_tension_type(context_tags)
            alert = TensionAlert(
                relationship_id=relationship_id,
                party_ids=party_ids,
                tension_score=round(new_score, 4),
                tension_type=tension_type,
                triggering_events=[event_id],
                context_summary=f"Tension detected ({', '.join(context_tags)}) score={new_score:.2f}",
                recommended_negotiation_type=tension_type,
            )
            await self.producer.emit(
                topic=TOPICS["NEGOTIATION_START"],
                key=relationship_id,
                value=alert.to_dict(),
            )
            await self._set_rate_limit(relationship_id)
            logger.info(f"TensionAlert fired for relationship {relationship_id}: score={new_score:.2f}")
            return alert

        return None

    def _classify_tension_type(self, context_tags: list[str]) -> str:
        tag_set = set(context_tags)
        if "financial" in tag_set:
            return "expense"
        if "scheduling" in tag_set:
            return "scheduling"
        if "sentiment_negative" in tag_set or "communication" in tag_set:
            return "communication"
        return "conflict"
