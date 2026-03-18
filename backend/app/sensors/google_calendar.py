"""Google Calendar sensor adapter for SYNAPSE."""
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.sensors.base import BaseSensorAdapter
from app.models.canonical_event import CanonicalEvent, EventSource

logger = logging.getLogger(__name__)


class GoogleCalendarAdapter(BaseSensorAdapter):
    """
    Processes Google Calendar push notifications via webhook.
    Endpoint: POST /webhooks/calendar/{user_id}
    """

    integration_name = "google_calendar"

    def normalize(self, raw_event: dict) -> CanonicalEvent:
        """Parse a Google Calendar push notification payload."""
        now = datetime.utcnow()

        # Extract fields from the Google Calendar notification
        event_start_str = raw_event.get("start", {}).get("dateTime") or raw_event.get("start", {}).get("date")
        event_start = datetime.fromisoformat(event_start_str.replace("Z", "+00:00")) if event_start_str else now

        party_ids = [self.user_id]
        for attendee in raw_event.get("attendees", []):
            if attendee.get("email") and attendee["email"] != self.user_id:
                party_ids.append(attendee["email"])

        return CanonicalEvent(
            id=uuid.uuid4(),
            source=EventSource.calendar,
            party_ids=party_ids,
            relationship_id=raw_event.get("relationship_id", uuid.uuid4()),
            pre_tension_score=0.30,  # will be recomputed
            payload_vector=None,
            timestamp=event_start,
            context_tags=["scheduling", "calendar_conflict"],
            processed=False,
            created_at=now,
        )

    def compute_pre_tension_score(self, event: CanonicalEvent) -> float:
        now = datetime.utcnow()
        hours_until = (event.timestamp.replace(tzinfo=None) - now).total_seconds() / 3600

        if hours_until <= 0:
            return self.score("same_day_conflict")  # Past-due / same day
        elif hours_until <= 24:
            return self.score("same_day_conflict")
        elif hours_until <= 72:
            return self.score("scheduling_conflict")
        return self.score("default")
