"""Splitwise sensor adapter for SYNAPSE — polling every 5 mins via Celery beat."""
import uuid
import logging
import httpx
from datetime import datetime
from typing import Optional

from app.sensors.base import BaseSensorAdapter
from app.models.canonical_event import CanonicalEvent, EventSource
from app.config import settings

logger = logging.getLogger(__name__)


class SplitwiseAdapter(BaseSensorAdapter):
    """
    Polls Splitwise API every 5 minutes for expense data.
    Detects imbalance in who is paying more than their share.
    """

    integration_name = "splitwise"
    SPLITWISE_API_BASE = "https://secure.splitwise.com/api/v3.0"

    def __init__(self, user_id: str, access_token: str):
        super().__init__(user_id)
        self.access_token = access_token

    async def fetch_expenses(self, group_id: Optional[str] = None, friend_id: Optional[str] = None) -> list:
        """Fetch expenses from Splitwise API."""
        params = {"limit": 50}
        if group_id:
            params["group_id"] = group_id
        if friend_id:
            params["friend_id"] = friend_id

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.SPLITWISE_API_BASE}/get_expenses",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params=params,
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json().get("expenses", [])

    def compute_expense_ratio(self, expenses: list) -> tuple[float, list[str]]:
        """Return (expense_ratio, party_ids) where ratio = user_paid / total."""
        total = 0.0
        user_paid = 0.0
        party_ids = {self.user_id}

        for expense in expenses:
            cost = float(expense.get("cost", 0))
            total += cost
            for user in expense.get("users", []):
                party_ids.add(str(user.get("user_id", "")))
                if str(user.get("user_id")) == self.user_id and user.get("paid_share"):
                    user_paid += float(user["paid_share"])

        ratio = (user_paid / total) if total > 0 else 0.0
        return ratio, list(party_ids)

    def normalize(self, raw_event: dict) -> CanonicalEvent:
        now = datetime.utcnow()
        ratio = raw_event.get("expense_ratio", 0.0)
        party_ids = raw_event.get("party_ids", [self.user_id])

        return CanonicalEvent(
            id=uuid.uuid4(),
            source=EventSource.splitwise,
            party_ids=party_ids,
            relationship_id=raw_event.get("relationship_id", uuid.uuid4()),
            pre_tension_score=0.30,
            payload_vector=None,
            timestamp=now,
            context_tags=["financial", "expense_imbalance"],
            processed=False,
            created_at=now,
        )

    def compute_pre_tension_score(self, event: CanonicalEvent) -> float:
        # Caller must inject expense_ratio into the raw_event before normalize
        return self.score("default")

    def score_expense_ratio(self, ratio: float) -> float:
        """Map expense imbalance ratio to a tension score."""
        if ratio > 0.75:
            return self.score("expense_imbalance_75")
        if ratio > 0.65:
            return self.score("expense_imbalance_65")
        return self.score("default")
