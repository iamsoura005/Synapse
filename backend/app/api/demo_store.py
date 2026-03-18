from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime, timedelta

DEMO_USER_ID = "demo-user"


def _iso(dt: datetime | None = None) -> str:
    return (dt or datetime.utcnow()).isoformat()


def _seed_round(round_number: int, party_ids: list[str], base_fairness: float) -> dict:
    turns = []
    for index, party in enumerate(party_ids):
        concession = max(3.0, 12.0 - (round_number * 1.5) - index)
        satisfaction = min(0.95, 0.62 + (round_number * 0.07) + (index * 0.03))
        turns.append(
            {
                "agent_id": party,
                "round": round_number,
                "stance": ["FIRM", "FLEXIBLE", "CONCEDING", "ACCEPTING"][min(round_number, 3)],
                "offer": {
                    "budget_split": f"{55 - round_number * 3}/{45 + round_number * 3}",
                    "timeline_days": max(3, 10 - round_number),
                },
                "concession_pct": round(concession, 1),
                "satisfaction_score": round(satisfaction, 2),
                "BATNA_score": 0.72,
                "fairness_index": round(min(0.96, base_fairness + round_number * 0.04), 2),
                "rationale": "Balanced concession to preserve long-term trust.",
            }
        )
    return {"round_number": round_number, "agent_turns": turns, "created_at": _iso()}


class DemoStore:
    def __init__(self):
        self.relationships: dict[str, dict] = {}
        self.negotiations: dict[str, dict] = {}
        self.negotiation_rounds: dict[str, list[dict]] = {}
        self.contracts: dict[str, dict] = {}
        self.integrations: dict[str, dict[str, bool]] = {}
        self._seed()

    def _seed(self) -> None:
        rel1 = str(uuid.uuid4())
        rel2 = str(uuid.uuid4())
        rel3 = str(uuid.uuid4())

        self.relationships[rel1] = {
            "id": rel1,
            "user_id": DEMO_USER_ID,
            "counterparty_id": "alex-chen",
            "counterparty_name": "Alex Chen",
            "relationship_type": "roommate",
            "health_score": 78.0,
            "trust_index": 0.74,
            "compatibility_score": 0.81,
            "negotiation_style": "collaborative",
            "total_negotiations": 11,
            "successful_resolutions": 9,
            "created_at": _iso(datetime.utcnow() - timedelta(days=220)),
        }
        self.relationships[rel2] = {
            "id": rel2,
            "user_id": DEMO_USER_ID,
            "counterparty_id": "jordan-kim",
            "counterparty_name": "Jordan Kim",
            "relationship_type": "colleague",
            "health_score": 65.0,
            "trust_index": 0.59,
            "compatibility_score": 0.69,
            "negotiation_style": "competitive",
            "total_negotiations": 7,
            "successful_resolutions": 5,
            "created_at": _iso(datetime.utcnow() - timedelta(days=180)),
        }
        self.relationships[rel3] = {
            "id": rel3,
            "user_id": DEMO_USER_ID,
            "counterparty_id": "sam-rivera",
            "counterparty_name": "Sam Rivera",
            "relationship_type": "friend",
            "health_score": 88.0,
            "trust_index": 0.86,
            "compatibility_score": 0.9,
            "negotiation_style": "accommodating",
            "total_negotiations": 5,
            "successful_resolutions": 5,
            "created_at": _iso(datetime.utcnow() - timedelta(days=300)),
        }

        n1 = str(uuid.uuid4())
        n2 = str(uuid.uuid4())

        self.negotiations[n1] = {
            "id": n1,
            "relationship_id": rel1,
            "status": "in_progress",
            "negotiation_type": "expense",
            "party_ids": [DEMO_USER_ID, "alex-chen"],
            "rounds_completed": 3,
            "final_satisfaction_scores": None,
            "shapley_allocation": None,
            "fairness_index": 0.79,
            "resolution": {
                "title": "Shared Utilities Rebalance",
                "summary": "Shift electricity and internet to a 52/48 split based on usage trend.",
                "terms": {
                    "billing_cycle_start": "next_month",
                    "split": {"demo-user": 52, "alex-chen": 48},
                    "review_after_days": 30,
                },
            },
            "started_at": _iso(datetime.utcnow() - timedelta(hours=2)),
            "completed_at": None,
        }
        self.negotiation_rounds[n1] = [
            _seed_round(1, [DEMO_USER_ID, "alex-chen"], 0.71),
            _seed_round(2, [DEMO_USER_ID, "alex-chen"], 0.74),
            _seed_round(3, [DEMO_USER_ID, "alex-chen"], 0.79),
        ]

        self.negotiations[n2] = {
            "id": n2,
            "relationship_id": rel3,
            "status": "completed",
            "negotiation_type": "scheduling",
            "party_ids": [DEMO_USER_ID, "sam-rivera"],
            "rounds_completed": 2,
            "final_satisfaction_scores": {"demo-user": 0.91, "sam-rivera": 0.9},
            "shapley_allocation": {"time_flexibility": 0.54, "location_flexibility": 0.46},
            "fairness_index": 0.9,
            "resolution": {
                "title": "Weekly Planning Cadence",
                "summary": "Move planning call to Sunday 7 PM with async notes fallback.",
                "terms": {
                    "meeting_day": "Sunday",
                    "meeting_time": "19:00",
                    "fallback": "shared_note",
                },
            },
            "started_at": _iso(datetime.utcnow() - timedelta(days=1)),
            "completed_at": _iso(datetime.utcnow() - timedelta(hours=20)),
        }
        self.negotiation_rounds[n2] = [
            _seed_round(1, [DEMO_USER_ID, "sam-rivera"], 0.84),
            _seed_round(2, [DEMO_USER_ID, "sam-rivera"], 0.9),
        ]

        contract_id = str(uuid.uuid4())
        self.contracts[contract_id] = {
            "id": contract_id,
            "negotiation_id": n2,
            "party_ids": [DEMO_USER_ID, "sam-rivera"],
            "clauses": [
                {
                    "clause_id": "c1",
                    "title": "Weekly Check-In",
                    "type": "milestone",
                    "description": "Review whether the new meeting cadence reduced last-minute conflicts.",
                    "trigger_status": "watching",
                    "trigger_condition": {"metric": "missed_meetings", "threshold": 1},
                },
                {
                    "clause_id": "c2",
                    "title": "Reschedule Guardrail",
                    "type": "adaptive",
                    "description": "If two consecutive meetings are skipped, auto-open renegotiation.",
                    "trigger_status": "watching",
                    "trigger_condition": {"metric": "consecutive_skips", "threshold": 2},
                },
            ],
            "status": "active",
            "polygon_hash": "demo-hash-1",
            "polygon_tx_hash": "0x" + "a" * 64,
            "polygon_scan_url": "https://amoy.polygonscan.com/tx/0x" + "a" * 64,
            "version": 1,
            "parent_contract_id": None,
            "created_at": _iso(datetime.utcnow() - timedelta(hours=18)),
            "expires_at": _iso(datetime.utcnow() + timedelta(days=90)),
        }

        self.integrations[DEMO_USER_ID] = {
            "google_calendar": True,
            "gmail": True,
            "slack": False,
            "splitwise": True,
        }

    def _ensure_user_integrations(self, user_id: str) -> dict[str, bool]:
        if user_id not in self.integrations:
            self.integrations[user_id] = {
                "google_calendar": False,
                "gmail": False,
                "slack": False,
                "splitwise": False,
            }
        return self.integrations[user_id]

    # Relationships
    def list_relationships(self, user_id: str) -> list[dict]:
        return [deepcopy(r) for r in self.relationships.values() if r["user_id"] == user_id]

    def get_relationship(self, relationship_id: str) -> dict | None:
        item = self.relationships.get(relationship_id)
        return deepcopy(item) if item else None

    def create_relationship(self, user_id: str, counterparty_id: str, relationship_type: str) -> dict:
        rel_id = str(uuid.uuid4())
        item = {
            "id": rel_id,
            "user_id": user_id,
            "counterparty_id": counterparty_id,
            "counterparty_name": counterparty_id.replace("-", " ").title(),
            "relationship_type": relationship_type,
            "health_score": 70.0,
            "trust_index": 0.55,
            "compatibility_score": 0.6,
            "negotiation_style": "collaborative",
            "total_negotiations": 0,
            "successful_resolutions": 0,
            "created_at": _iso(),
        }
        self.relationships[rel_id] = item
        return deepcopy(item)

    def delete_relationship(self, relationship_id: str) -> bool:
        if relationship_id in self.relationships:
            del self.relationships[relationship_id]
            return True
        return False

    def get_relationship_graph(self, relationship_id: str) -> dict | None:
        rel = self.relationships.get(relationship_id)
        if not rel:
            return None
        return {
            "nodes": [
                {"id": rel["user_id"], "name": "You", "type": "self"},
                {
                    "id": rel["counterparty_id"],
                    "name": rel["counterparty_name"],
                    "type": "contact",
                    "health_score": rel["health_score"],
                },
            ],
            "edges": [
                {
                    "source": rel["user_id"],
                    "target": rel["counterparty_id"],
                    "health_score": rel["health_score"],
                    "relationship_type": rel["relationship_type"],
                    "tension_trend": "improving" if rel["health_score"] > 70 else "stable",
                    "active_contracts": len(
                        [c for c in self.contracts.values() if rel["user_id"] in c["party_ids"] and rel["counterparty_id"] in c["party_ids"]]
                    ),
                }
            ],
        }

    def get_relationship_insights(self, relationship_id: str) -> list[dict]:
        rel = self.relationships.get(relationship_id)
        if not rel:
            return []
        success_rate = 0.0
        if rel["total_negotiations"]:
            success_rate = rel["successful_resolutions"] / rel["total_negotiations"]
        return [
            {
                "insight": "Trust is stable and can support faster negotiation cycles.",
                "confidence": round(min(0.95, rel["trust_index"] + 0.1), 2),
                "actionable_suggestion": "Use 1-round proposals for low-risk decisions.",
            },
            {
                "insight": "Outcome quality correlates strongly with explicit timelines.",
                "confidence": round(min(0.95, 0.55 + rel["compatibility_score"] * 0.4), 2),
                "actionable_suggestion": "Attach target dates to all proposed terms.",
            },
            {
                "insight": f"Historical resolution rate is {success_rate * 100:.0f}%.",
                "confidence": 0.82,
                "actionable_suggestion": "Escalate only after two failed rounds to preserve rapport.",
            },
        ]

    # Negotiations
    def list_negotiations(self, user_id: str) -> list[dict]:
        return [deepcopy(n) for n in self.negotiations.values() if user_id in n["party_ids"]]

    def get_negotiation(self, negotiation_id: str) -> dict | None:
        item = self.negotiations.get(negotiation_id)
        return deepcopy(item) if item else None

    def get_rounds(self, negotiation_id: str) -> list[dict]:
        return deepcopy(self.negotiation_rounds.get(negotiation_id, []))

    def approve_negotiation(self, negotiation_id: str) -> dict | None:
        item = self.negotiations.get(negotiation_id)
        if not item:
            return None
        item["status"] = "completed"
        item["completed_at"] = _iso()
        return deepcopy(item)

    def modify_negotiation(self, negotiation_id: str, modification: dict) -> dict | None:
        item = self.negotiations.get(negotiation_id)
        if not item:
            return None
        terms = item.setdefault("resolution", {}).setdefault("terms", {})
        terms.update(modification)
        item["status"] = "completed"
        item["completed_at"] = _iso()
        item["fairness_index"] = round(min(0.97, float(item.get("fairness_index") or 0.75) + 0.03), 2)
        item["rounds_completed"] = int(item.get("rounds_completed") or 0) + 1
        rounds = self.negotiation_rounds.setdefault(negotiation_id, [])
        rounds.append(_seed_round(item["rounds_completed"], item["party_ids"], item["fairness_index"]))
        return deepcopy(item)

    def override_negotiation(self, negotiation_id: str, custom_terms: dict) -> dict | None:
        item = self.negotiations.get(negotiation_id)
        if not item:
            return None
        item["status"] = "overridden"
        item["completed_at"] = _iso()
        item["resolution"] = {
            "type": "user_override",
            "title": "User-defined terms",
            "summary": "Resolution manually overridden by user.",
            "terms": custom_terms,
            "overridden_at": _iso(),
        }
        return deepcopy(item)

    def delay_negotiation(self, negotiation_id: str, delay_hours: int = 2) -> dict | None:
        item = self.negotiations.get(negotiation_id)
        if not item:
            return None
        item["status"] = "pending"
        item["retry_after_hours"] = delay_hours
        return deepcopy(item)

    def start_manual_negotiation(
        self,
        negotiation_type: str,
        party_ids: list[str],
        context: str,
        urgency: str,
        relationship_id: str | None,
    ) -> dict:
        neg_id = str(uuid.uuid4())
        rounds_to_run = 2 if urgency == "low" else 3 if urgency == "medium" else 4
        fairness = 0.72 if urgency == "high" else 0.8
        rounds = [_seed_round(i, party_ids, fairness) for i in range(1, rounds_to_run + 1)]
        resolution = {
            "title": "Manual Negotiation Resolution",
            "summary": f"Negotiation converged after {rounds_to_run} rounds.",
            "context": context,
            "terms": {
                "cadence": "weekly",
                "communication_channel": "async + checkpoint",
                "urgency": urgency,
            },
        }
        item = {
            "id": neg_id,
            "relationship_id": relationship_id,
            "status": "completed",
            "negotiation_type": negotiation_type,
            "party_ids": party_ids,
            "rounds_completed": rounds_to_run,
            "final_satisfaction_scores": {party: round(0.78 + index * 0.05, 2) for index, party in enumerate(party_ids)},
            "shapley_allocation": {"collaboration": 0.51, "speed": 0.49},
            "fairness_index": fairness,
            "resolution": resolution,
            "started_at": _iso(datetime.utcnow() - timedelta(minutes=25)),
            "completed_at": _iso(),
        }
        self.negotiations[neg_id] = item
        self.negotiation_rounds[neg_id] = rounds
        return deepcopy(item)

    # Contracts
    def list_contracts(self, user_id: str) -> list[dict]:
        return [deepcopy(c) for c in self.contracts.values() if user_id in c["party_ids"]]

    def get_contract(self, contract_id: str) -> dict | None:
        item = self.contracts.get(contract_id)
        return deepcopy(item) if item else None

    def create_contract(self, negotiation_id: str, party_ids: list[str], clauses: list[dict]) -> dict:
        contract_id = str(uuid.uuid4())
        contract = {
            "id": contract_id,
            "negotiation_id": negotiation_id,
            "party_ids": party_ids,
            "clauses": clauses,
            "status": "active",
            "polygon_hash": f"demo-hash-{contract_id[:8]}",
            "polygon_tx_hash": "0x" + contract_id.replace("-", "")[:64].ljust(64, "0"),
            "polygon_scan_url": "https://amoy.polygonscan.com/tx/0x" + contract_id.replace("-", "")[:64].ljust(64, "0"),
            "version": 1,
            "parent_contract_id": None,
            "created_at": _iso(),
            "expires_at": _iso(datetime.utcnow() + timedelta(days=120)),
        }
        self.contracts[contract_id] = contract
        return deepcopy(contract)

    # Integrations
    def connect_integration(self, user_id: str, integration_name: str) -> dict:
        data = self._ensure_user_integrations(user_id)
        data[integration_name] = True
        return deepcopy(data)

    def disconnect_integration(self, user_id: str, integration_name: str) -> dict:
        data = self._ensure_user_integrations(user_id)
        data[integration_name] = False
        return deepcopy(data)

    def get_integration_status(self, user_id: str) -> dict:
        return deepcopy(self._ensure_user_integrations(user_id))


store = DemoStore()
