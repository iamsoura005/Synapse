"""Base sensor adapter abstract class for SYNAPSE."""
import abc
import uuid
import logging
from datetime import datetime
from typing import Optional
from app.models.canonical_event import CanonicalEvent, EventSource
from app.kafka.producer import synapse_producer
from app.kafka.topics import TOPICS

logger = logging.getLogger(__name__)

# Pre-tension score heuristics
PRETENSION_SCORES = {
    "scheduling_conflict":     0.70,
    "same_day_conflict":       0.85,
    "response_latency_48h":   0.55,
    "expense_imbalance_65":   0.71,
    "expense_imbalance_75":   0.82,
    "negative_sentiment_07":  0.68,
    "missed_deadline":         0.65,
    "email_unanswered_5":      0.60,
    "email_unread_important":  0.55,
    "response_time_72h":       0.65,
    "default":                 0.30,
}


class BaseSensorAdapter(abc.ABC):
    """Abstract base class for all SYNAPSE sensor adapters."""

    integration_name: str = "base"

    def __init__(self, user_id: str):
        self.user_id = user_id

    @abc.abstractmethod
    def normalize(self, raw_event: dict) -> CanonicalEvent:
        """Convert a raw integration event into a CanonicalEvent."""
        ...

    @abc.abstractmethod
    def compute_pre_tension_score(self, event: CanonicalEvent) -> float:
        """Return a 0.0–1.0 tension score for this event."""
        ...

    async def process_and_emit(self, raw_event: dict) -> Optional[CanonicalEvent]:
        """Normalize, score, and emit an event to Kafka.  Returns the CanonicalEvent."""
        try:
            event = self.normalize(raw_event)
            event.pre_tension_score = self.compute_pre_tension_score(event)

            payload = {
                "event_id":         str(event.id),
                "source":           event.source.value,
                "party_ids":        event.party_ids,
                "relationship_id":  str(event.relationship_id),
                "pre_tension_score": event.pre_tension_score,
                "context_tags":     event.context_tags,
                "timestamp":        event.timestamp.isoformat(),
            }

            await synapse_producer.emit(
                topic=TOPICS["TENSION_SIGNALS"],
                key=str(event.relationship_id),
                value=payload,
            )
            logger.info(
                f"[{self.integration_name}] Emitted event {event.id} "
                f"pre_tension={event.pre_tension_score:.2f}"
            )
            return event
        except Exception as e:
            logger.error(f"[{self.integration_name}] Failed to process event: {e}")
            return None

    @classmethod
    def score(cls, key: str) -> float:
        return PRETENSION_SCORES.get(key, PRETENSION_SCORES["default"])
