"""Slack sensor adapter for SYNAPSE."""
import uuid
import logging
from datetime import datetime
from typing import Optional

from app.sensors.base import BaseSensorAdapter
from app.models.canonical_event import CanonicalEvent, EventSource

logger = logging.getLogger(__name__)


class SlackAdapter(BaseSensorAdapter):
    """
    Handles Slack Events API webhook payloads.
    Events: message.channels, reaction_added, member_joined_channel.
    Sentiment scoring: distilbert SST-2 (text discarded after scoring).
    """

    integration_name = "slack"
    _sentiment_pipeline = None  # lazy-loaded

    def _get_sentiment_pipeline(self):
        if self._sentiment_pipeline is None:
            try:
                from transformers import pipeline as hf_pipeline
                self._sentiment_pipeline = hf_pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    truncation=True,
                    max_length=512,
                )
            except ImportError:
                logger.warning("transformers not installed — sentiment analysis disabled")
        return self._sentiment_pipeline

    def _score_sentiment(self, text: str) -> float:
        """Returns negative probability 0.0–1.0. Text is discarded immediately."""
        pipe = self._get_sentiment_pipeline()
        if pipe is None or not text:
            return 0.0
        result = pipe(text[:512])[0]
        if result["label"] == "NEGATIVE":
            return result["score"]
        return 1.0 - result["score"]

    def normalize(self, raw_event: dict) -> CanonicalEvent:
        now = datetime.utcnow()
        event_type = raw_event.get("type", "")
        inner = raw_event.get("event", raw_event)

        user_id = inner.get("user", self.user_id)
        channel = inner.get("channel", "")
        party_ids = [user_id, self.user_id] if user_id != self.user_id else [self.user_id]

        # Score sentiment on message text, then discard the text
        text = inner.get("text", "")
        neg_score = self._score_sentiment(text)
        # text is not stored past this point

        return CanonicalEvent(
            id=uuid.uuid4(),
            source=EventSource.slack,
            party_ids=list(set(party_ids)),
            relationship_id=raw_event.get("relationship_id", uuid.uuid4()),
            pre_tension_score=neg_score,  # set directly from sentiment
            payload_vector=None,
            timestamp=now,
            context_tags=["communication", "sentiment_negative"],
            processed=False,
            created_at=now,
        )

    def compute_pre_tension_score(self, event: CanonicalEvent) -> float:
        # Score already embedded at normalize time from sentiment
        if event.pre_tension_score > 0.70:
            return self.score("negative_sentiment_07")
        return event.pre_tension_score
