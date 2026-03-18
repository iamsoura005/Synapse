"""Kafka Consumer base class and SYNAPSE-specific consumers."""
import asyncio
import json
import logging
import signal
from typing import Callable, Awaitable
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from app.config import settings
from app.kafka.topics import TOPICS
from app.kafka.producer import synapse_producer

logger = logging.getLogger(__name__)

Handler = Callable[[dict], Awaitable[None]]


class BaseConsumer:
    """Async-compatible Kafka consumer with dead-letter queue and graceful shutdown."""

    MAX_RETRIES = 3
    POLL_TIMEOUT_MS = 1000

    def __init__(self, topic: str, group_id: str, handler: Handler):
        self.topic = topic
        self.group_id = group_id
        self.handler = handler
        self._running = False
        self._consumer: KafkaConsumer | None = None

    def _build_consumer(self) -> KafkaConsumer:
        return KafkaConsumer(
            self.topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=self.group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            consumer_timeout_ms=self.POLL_TIMEOUT_MS,
        )

    async def run(self):
        """Main consume loop — runs until shutdown."""
        self._running = True
        self._consumer = self._build_consumer()
        logger.info(f"[{self.group_id}] Consumer started on topic: {self.topic}")

        try:
            while self._running:
                try:
                    records = self._consumer.poll(timeout_ms=self.POLL_TIMEOUT_MS)
                    for _tp, messages in records.items():
                        for message in messages:
                            await self._process_with_retry(message.value)
                except KafkaError as e:
                    logger.error(f"[{self.group_id}] Kafka poll error: {e}")
                    await asyncio.sleep(1)
        finally:
            if self._consumer:
                self._consumer.close()
            logger.info(f"[{self.group_id}] Consumer stopped.")

    async def _process_with_retry(self, payload: dict):
        for attempt in range(self.MAX_RETRIES):
            try:
                await self.handler(payload)
                return
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"[{self.group_id}] Handler failed (attempt {attempt+1}): {e}")
                    await asyncio.sleep(0.5 * (2 ** attempt))
                else:
                    logger.error(f"[{self.group_id}] Handler permanently failed. Sending to dead letters.")
                    await synapse_producer.emit(
                        TOPICS["DEAD_LETTERS"],
                        key="dead-letter",
                        value={
                            "original_topic": self.topic,
                            "group_id": self.group_id,
                            "payload": payload,
                            "error": str(e),
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )

    def stop(self):
        self._running = False


# ─── Concrete consumers ───────────────────────────────────────────────────────

class TensionSignalConsumer(BaseConsumer):
    def __init__(self, handler: Handler):
        super().__init__(TOPICS["TENSION_SIGNALS"], "sensor-agents", handler)


class NegotiationStartConsumer(BaseConsumer):
    def __init__(self, handler: Handler):
        super().__init__(TOPICS["NEGOTIATION_START"], "negotiation-engine", handler)


class ResolutionQueueConsumer(BaseConsumer):
    def __init__(self, handler: Handler):
        super().__init__(TOPICS["RESOLUTION_QUEUE"], "emotion-gate", handler)


class DeliveryReadyConsumer(BaseConsumer):
    def __init__(self, handler: Handler):
        super().__init__(TOPICS["DELIVERY_READY"], "delivery-layer", handler)


class ContractEventsConsumer(BaseConsumer):
    def __init__(self, handler: Handler):
        super().__init__(TOPICS["CONTRACT_EVENTS"], "contract-runtime", handler)
