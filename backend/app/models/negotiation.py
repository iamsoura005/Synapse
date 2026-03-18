import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from app.database.postgres import Base
from sqlalchemy import Enum as SQLEnum
import enum

class NegotiationStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    timed_out = "timed_out"
    overridden = "overridden"

class NegotiationType(str, enum.Enum):
    expense = "expense"
    scheduling = "scheduling"
    freelance = "freelance"
    roommate = "roommate"
    group_trip = "group_trip"
    conflict = "conflict"

class Negotiation(Base):
    __tablename__ = "negotiations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    relationship_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("relationship_profiles.id"))
    status: Mapped[NegotiationStatus] = mapped_column(SQLEnum(NegotiationStatus), default=NegotiationStatus.pending)
    negotiation_type: Mapped[NegotiationType] = mapped_column(SQLEnum(NegotiationType))
    party_ids: Mapped[list[str]] = mapped_column(ARRAY(String))
    rounds_completed: Mapped[int] = mapped_column(Integer, default=0)
    final_satisfaction_scores: Mapped[dict] = mapped_column(JSONB, nullable=True)
    shapley_allocation: Mapped[dict] = mapped_column(JSONB, nullable=True)
    fairness_index: Mapped[float] = mapped_column(Float, nullable=True)
    resolution: Mapped[dict] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

class NegotiationRound(Base):
    __tablename__ = "negotiation_rounds"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    negotiation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("negotiations.id"))
    round_number: Mapped[int] = mapped_column(Integer)
    agent_turns: Mapped[list[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
