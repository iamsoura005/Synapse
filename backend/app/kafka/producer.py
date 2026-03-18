"""Async Kafka producer wrapper for SYNAPSE."""
import json
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
from app.config import settings
from app.kafka.topics import TOPICS

logger = logging.getLogger(__name__)


def _default_serializer(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class SynapseProducer:
    """Thread-safe Kafka producer with automatic audit logging and retry logic."""

    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 0.5  # seconds

    def __init__(self):
        self._producer: Optional[KafkaProducer] = None

    def _get_producer(self) -> KafkaProducer:
        if self._producer is None:
            self._producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=_default_serializer).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retries=self.MAX_RETRIES,
            )
        return self._producer

    async def emit(
        self,
        topic: str,
        key: str,
        value: dict,
        headers: Optional[dict] = None,
    ) -> None:
        """Emit a message to Kafka with exponential backoff retry."""
        producer = self._get_producer()
        kafka_headers = [(k, v.encode()) for k, v in (headers or {}).items()]

        for attempt in range(self.MAX_RETRIES):
            try:
                future = producer.send(topic, key=key, value=value, headers=kafka_headers)
                future.get(timeout=10)  # block until sent or error

                # Auto-audit every emission (except audit_log itself to avoid recursion)
                if topic != TOPICS["AUDIT_LOG"]:
                    audit_payload = {
                        "event": "kafka_emit",
                        "topic": topic,
                        "key": key,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    producer.send(TOPICS["AUDIT_LOG"], key=key, value=audit_payload)
                return
            except KafkaError as e:
                if attempt < self.MAX_RETRIES - 1:
                    wait = self.RETRY_BACKOFF_BASE * (2 ** attempt)
                    logger.warning(f"Kafka emit attempt {attempt+1} failed for topic {topic}: {e}. Retrying in {wait}s.")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Kafka emit permanently failed for topic {topic} after {self.MAX_RETRIES} attempts: {e}")
                    raise

    def close(self):
        if self._producer:
            self._producer.flush()
            self._producer.close()
            self._producer = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.close()


# Singleton instance
synapse_producer = SynapseProducer()
