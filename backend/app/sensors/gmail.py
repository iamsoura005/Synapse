"""Gmail sensor adapter for SYNAPSE — metadata only, no body access."""
import uuid
import logging
from datetime import datetime, timedelta

from app.sensors.base import BaseSensorAdapter
from app.models.canonical_event import CanonicalEvent, EventSource

logger = logging.getLogger(__name__)


class GmailAdapter(BaseSensorAdapter):
    """
    Handles Google Pub/Sub subscription events from Gmail.
    PRIVACY: only reads from, to, date, label_ids, thread_id — never body.
    """

    integration_name = "gmail"

    def normalize(self, raw_event: dict) -> CanonicalEvent:
        now = datetime.utcnow()
        message = raw_event.get("message", raw_event)

        sender = message.get("from", "unknown")
        recipients = message.get("to", "").split(",")
        party_ids = [sender.strip()] + [r.strip() for r in recipients if r.strip()]

        timestamp_str = message.get("date")
        try:
            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else now
        except ValueError:
            timestamp = now

        return CanonicalEvent(
            id=uuid.uuid4(),
            source=EventSource.gmail,
            party_ids=party_ids,
            relationship_id=raw_event.get("relationship_id", uuid.uuid4()),
            pre_tension_score=0.30,
            payload_vector=None,
            timestamp=timestamp,
            context_tags=["communication", "email_lag"],
            processed=False,
            created_at=now,
        )

    def compute_pre_tension_score(self, event: CanonicalEvent) -> float:
        # Scoring is heuristic — real signal comes from metadata injected by caller
        # Callers should inject these keys in the raw_event dict for overrides:
        #   unanswered_count, is_important_unread, response_hours
        return self.score("default")

    def score_from_metadata(
        self,
        unanswered_count: int = 0,
        is_important_unread: bool = False,
        response_hours: float = 0,
    ) -> float:
        """Compute score from Gmail thread metadata signals."""
        if unanswered_count > 5:
            return self.score("email_unanswered_5")
        if is_important_unread:
            return self.score("email_unread_important")
        if response_hours > 72:
            return self.score("response_time_72h")
        return self.score("default")
