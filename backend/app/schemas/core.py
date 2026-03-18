from pydantic import BaseModel, ConfigDict, Field, model_validator
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.models.canonical_event import EventSource
from app.models.negotiation import NegotiationStatus, NegotiationType
from app.models.contract import ContractStatus
from app.models.relationship import RelationshipType, NegotiationStyle

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseSchema):
    email: str
    name: str

class UserCreateRequest(UserBase):
    tension_threshold: Optional[int] = 65

class UserResponse(UserBase):
    id: uuid.UUID
    emotion_readiness_score: float
    tension_threshold: int
    connected_integrations: List[str]
    created_at: datetime

class CanonicalEventResponse(BaseSchema):
    id: uuid.UUID
    source: EventSource
    party_ids: List[str]
    relationship_id: uuid.UUID
    pre_tension_score: float
    timestamp: datetime
    context_tags: List[str]
    processed: bool
    created_at: datetime

class NegotiationResponse(BaseSchema):
    id: uuid.UUID
    relationship_id: uuid.UUID
    status: NegotiationStatus
    negotiation_type: NegotiationType
    party_ids: List[str]
    rounds_completed: int
    final_satisfaction_scores: Optional[Dict[str, float]]
    shapley_allocation: Optional[Dict[str, float]]
    fairness_index: Optional[float]
    resolution: Optional[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime]

class ContractCreateRequest(BaseSchema):
    negotiation_id: uuid.UUID
    party_ids: List[str]
    clauses: List[Dict[str, Any]]

class LivingContractResponse(BaseSchema):
    id: uuid.UUID
    negotiation_id: uuid.UUID
    party_ids: List[str]
    clauses: List[Dict[str, Any]]
    status: ContractStatus
    polygon_hash: Optional[str]
    polygon_tx_hash: Optional[str]
    polygon_scan_url: Optional[str]
    version: int
    created_at: datetime
