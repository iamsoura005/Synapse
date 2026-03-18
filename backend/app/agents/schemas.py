"""
Shared agent JSON schemas for SYNAPSE agents.
These Pydantic models represent the structured outputs from each agent.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime


class AgentTurn(BaseModel):
    """A single agent turn in a negotiation round — all fields are REQUIRED."""
    agent_id: str
    round: int
    stance: str  # "FIRM" | "FLEXIBLE" | "CONCEDING" | "ACCEPTING"
    offer: Dict[str, Any]
    concession_pct: float = Field(ge=0, le=100, description="% of original position conceded this round")
    satisfaction_score: float = Field(ge=0, le=1)
    BATNA_score: float = Field(ge=0, le=1)
    fairness_index: float = Field(ge=0, le=1)
    rationale: str = Field(max_length=100)


class PartyProfile(BaseModel):
    party_id: str
    negotiation_style: str
    historical_satisfaction_avg: float
    typical_concession_pct: float
    BATNA_estimate: str
    communication_preferences: List[str]


class RelationshipContext(BaseModel):
    trust_index: float
    health_score: float
    total_past_negotiations: int
    successful_resolution_rate: float


class ContextBrief(BaseModel):
    brief_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_id: str
    tension_type: str
    party_profiles: List[PartyProfile]
    relationship_context: RelationshipContext
    market_data: Dict[str, Any] = {}
    recommended_approach: str
    estimated_rounds: int
    risk_factors: List[str]


class TensionAlert(BaseModel):
    alert_id: str
    relationship_id: str
    party_ids: List[str]
    tension_score: float
    tension_type: str
    triggering_events: List[str]
    context_summary: str
    recommended_negotiation_type: str
    timestamp: str


class GatingDecision(BaseModel):
    cleared: bool
    next_check_at: Optional[datetime]
    party_readiness: Dict[str, float]
    forced: bool = False  # True when 48h hard cap reached
