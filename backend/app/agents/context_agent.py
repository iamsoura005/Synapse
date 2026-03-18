"""Context Agent — builds a ContextBrief from relationship data before negotiation starts."""
import json
import logging
from datetime import datetime
from typing import Optional
import google.generativeai as genai

from app.config import settings
from app.agents.schemas import ContextBrief, TensionAlert, PartyProfile, RelationshipContext
from app.graph.neo4j_client import Neo4jClient
from app.kafka.producer import SynapseProducer
from app.kafka.topics import TOPICS

logger = logging.getLogger(__name__)

TAVILY_SEARCH_TYPES = {"freelance", "group_trip", "marketplace"}
TAVILY_CACHE_TTL = 3600  # 1 hour

TAVILY_QUERY_TEMPLATES = {
    "freelance":   "average {role} freelance rate {location} {year}",
    "group_trip":  "average cost {destination} trip {duration}",
    "marketplace": "{item} market price {condition}",
}


class ContextAgent:
    """
    Triggered by TensionAlert.
    Queries Neo4j + PostgreSQL negotiation history, optionally grabs market data via Tavily,
    synthesizes everything with Gemini 1.5 Pro into a ContextBrief.
    """

    def __init__(self, neo4j_client: Neo4jClient, kafka_producer: SynapseProducer, redis_client=None):
        self.neo4j = neo4j_client
        self.producer = kafka_producer
        self.redis = redis_client

        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._gemini_pro = genai.GenerativeModel(
            settings.GEMINI_PRO_MODEL,
            generation_config=genai.GenerationConfig(temperature=0.2, top_p=0.95),
        )

    async def build_context_brief(self, alert: TensionAlert) -> ContextBrief:
        # Step 1: Fetch Neo4j relationship data
        graph_ctx = await self.neo4j.get_relationship_context(alert.relationship_id)
        style_profiles = {}
        for pid in alert.party_ids:
            style_profiles[pid] = await self.neo4j.get_negotiation_style_profile(pid)

        # Step 2: Optional Tavily market data
        market_data = {}
        if alert.tension_type in TAVILY_SEARCH_TYPES and self.redis:
            market_data = await self._get_market_data(alert)

        # Step 3: Synthesize with Gemini 1.5 Pro
        brief = await self._synthesize_with_gemini(alert, graph_ctx, style_profiles, market_data)

        # Step 4: Emit to Kafka
        await self.producer.emit(
            topic=TOPICS["NEGOTIATION_START"],
            key=alert.relationship_id,
            value={"type": "context_brief", **brief.model_dump()},
        )

        return brief

    async def _get_market_data(self, alert: TensionAlert) -> dict:
        """Fetch from Tavily with Redis caching. Max 2 calls per ContextBrief."""
        cache_key = f"tavily:{alert.tension_type}:{alert.relationship_id}"
        if self.redis:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=settings.TAVILY_API_KEY)
            template = TAVILY_QUERY_TEMPLATES.get(alert.tension_type, "")
            query = template.format(
                role="software engineer",
                location="global",
                year=datetime.utcnow().year,
                destination="Europe",
                duration="7 days",
                item="generic item",
                condition="good",
            )
            result = client.search(query, max_results=3)
            data = {"query": query, "results": result.get("results", [])}
            if self.redis:
                await self.redis.setex(cache_key, TAVILY_CACHE_TTL, json.dumps(data))
            return data
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
            return {}

    async def _synthesize_with_gemini(
        self,
        alert: TensionAlert,
        graph_ctx: dict,
        style_profiles: dict,
        market_data: dict,
    ) -> ContextBrief:
        prompt = f"""
You are SYNAPSE's Context Agent. Synthesize a ContextBrief from these inputs.
Return ONLY valid JSON matching the ContextBrief schema.

TensionAlert:
{json.dumps(alert.model_dump(), indent=2)}

Relationship Graph Context:
{json.dumps(graph_ctx, indent=2, default=str)}

Party Negotiation Style Profiles:
{json.dumps(style_profiles, indent=2)}

Market Data:
{json.dumps(market_data, indent=2)}

Output schema:
{{
  "brief_id": "uuid",
  "alert_id": "{alert.alert_id}",
  "tension_type": "{alert.tension_type}",
  "party_profiles": [
    {{
      "party_id": "string",
      "negotiation_style": "collaborative|competitive|avoidant|accommodating",
      "historical_satisfaction_avg": 0.0,
      "typical_concession_pct": 0.0,
      "BATNA_estimate": "string",
      "communication_preferences": ["string"]
    }}
  ],
  "relationship_context": {{
    "trust_index": 0.0,
    "health_score": 0.0,
    "total_past_negotiations": 0,
    "successful_resolution_rate": 0.0
  }},
  "market_data": {{}},
  "recommended_approach": "collaborative",
  "estimated_rounds": 2,
  "risk_factors": ["string"]
}}
Return valid JSON only.
"""
        try:
            response = self._gemini_pro.generate_content(prompt)
            raw = response.text.strip().removeprefix("```json").removesuffix("```").strip()
            data = json.loads(raw)
            return ContextBrief(**data)
        except Exception as e:
            logger.error(f"Gemini ContextBrief synthesis failed: {e}")
            # Return a safe fallback brief
            profiles = [
                PartyProfile(
                    party_id=pid,
                    negotiation_style="collaborative",
                    historical_satisfaction_avg=0.75,
                    typical_concession_pct=10.0,
                    BATNA_estimate="Walk away from the deal",
                    communication_preferences=["async"],
                )
                for pid in alert.party_ids
            ]
            rel = graph_ctx.get("relationship", {})
            return ContextBrief(
                alert_id=alert.alert_id,
                tension_type=alert.tension_type,
                party_profiles=profiles,
                relationship_context=RelationshipContext(
                    trust_index=rel.get("trust_index", 0.5),
                    health_score=rel.get("health_score", 70.0),
                    total_past_negotiations=0,
                    successful_resolution_rate=0.75,
                ),
                market_data=market_data,
                recommended_approach="collaborative",
                estimated_rounds=3,
                risk_factors=[alert.tension_type],
            )
