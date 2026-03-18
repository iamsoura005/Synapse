"""Living Contract Runtime — monitors trigger conditions for active contracts."""
import logging
from datetime import datetime, timedelta
from typing import Optional
from app.kafka.producer import synapse_producer
from app.kafka.topics import TOPICS

logger = logging.getLogger(__name__)


class ContractRuntime:
    """
    Celery beat task running every 5 minutes.
    Evaluates each active contract's clause trigger conditions.
    Emits to Kafka when a clause fires.
    """

    def __init__(self, db_session_factory, redis_client):
        self.db_session_factory = db_session_factory
        self.redis = redis_client

    async def check_all_triggers(self):
        """Fetch all active contracts and evaluate clauses."""
        from sqlalchemy import select
        from app.models.contract import LivingContract, ContractStatus

        async with self.db_session_factory() as session:
            result = await session.execute(
                select(LivingContract).where(LivingContract.status == ContractStatus.active)
            )
            contracts = result.scalars().all()

        for contract in contracts:
            for clause in (contract.clauses or []):
                triggered = await self.evaluate_trigger(clause, contract)
                if triggered:
                    await self._on_clause_triggered(clause, contract)

    async def evaluate_trigger(self, clause: dict, contract) -> bool:
        """
        Evaluate a single clause trigger condition.
        Returns True if the clause should fire.
        """
        clause_type    = clause.get("type", "static")
        trigger_status = clause.get("trigger_status", "watching")

        if trigger_status == "triggered":
            return False  # already triggered, don't re-fire

        now = datetime.utcnow()

        if clause_type == "expiry":
            expires_at_str = clause.get("terms", {}).get("expires_at")
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                if now >= expires_at:
                    return True
                if (expires_at - now).days <= 7:
                    logger.info(f"Contract {contract.id} clause {clause.get('clause_id')} expiring in ≤7 days")

        elif clause_type == "adaptive":
            cond = clause.get("trigger_condition", {})
            metric     = cond.get("metric")
            threshold  = cond.get("threshold", 0.15)
            direction  = cond.get("direction", "increase")
            if metric:
                current = await self._get_metric(metric, contract)
                baseline = clause.get("terms", {}).get("baseline_value", 0)
                if direction == "increase" and current - baseline > threshold:
                    return True
                if direction == "decrease" and baseline - current > threshold:
                    return True

        elif clause_type == "escalation":
            cond              = clause.get("trigger_condition", {})
            metric            = cond.get("metric")
            original_estimate = cond.get("original_estimate", 0)
            threshold_pct     = cond.get("threshold_pct", 20)
            if metric and original_estimate:
                current = await self._get_metric(metric, contract)
                pct_change = abs(current - original_estimate) / max(original_estimate, 1) * 100
                if pct_change > threshold_pct:
                    return True

        elif clause_type == "milestone":
            cond = clause.get("trigger_condition", {})
            event_type = cond.get("event_type")
            if event_type:
                completed = await self._check_milestone_event(event_type, contract)
                return completed

        return False

    async def _get_metric(self, metric: str, contract) -> float:
        """Retrieve current metric value from Redis cache."""
        key = f"metric:{metric}:{contract.id}"
        raw = await self.redis.get(key)
        return float(raw) if raw else 0.0

    async def _check_milestone_event(self, event_type: str, contract) -> bool:
        key = f"milestone:{event_type}:{contract.id}"
        return await self.redis.exists(key) == 1

    async def _on_clause_triggered(self, clause: dict, contract):
        """Update clause status and emit to Kafka for re-negotiation."""
        logger.info(
            f"Clause triggered: contract={contract.id} "
            f"clause_id={clause.get('clause_id')} type={clause.get('type')}"
        )

        await synapse_producer.emit(
            topic=TOPICS["CONTRACT_EVENTS"],
            key=str(contract.id),
            value={
                "event": "clause_triggered",
                "contract_id": str(contract.id),
                "clause_id": clause.get("clause_id"),
                "clause_type": clause.get("type"),
                "party_ids": contract.party_ids,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def auto_renegotiate_clause(self, clause: dict, contract):
        """
        Re-negotiate only the triggered clause.
        Creates a focused TensionAlert with tension_type = "contract_trigger".
        """
        alert_payload = {
            "alert_id":                    f"contract-trigger-{clause.get('clause_id')}",
            "relationship_id":             str(contract.id),
            "party_ids":                   contract.party_ids,
            "tension_score":               0.75,
            "tension_type":                "contract_trigger",
            "triggering_events":           [str(contract.id)],
            "context_summary":             f"Clause '{clause.get('title')}' has been triggered. Re-negotiation required.",
            "recommended_negotiation_type": "conflict",
            "timestamp":                   datetime.utcnow().isoformat(),
            "original_clause":             clause,  # Both parties use original terms as BATNA
        }
        await synapse_producer.emit(
            topic=TOPICS["NEGOTIATION_START"],
            key=str(contract.id),
            value=alert_payload,
        )
