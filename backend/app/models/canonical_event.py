import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.database.postgres import Base
import enum
from sqlalchemy import Enum as SQLEnum

class EventSource(str, enum.Enum):
    calendar = "calendar"
    gmail = "gmail"
    slack = "slack"
    telegram = "telegram"
    splitwise = "splitwise"
    upi = "upi"
    linear = "linear"
    notion = "notion"

class CanonicalEvent(Base):
    __tablename__ = "canonical_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[EventSource] = mapped_column(SQLEnum(EventSource))
    party_ids: Mapped[list[str]] = mapped_column(ARRAY(String))
    relationship_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("relationship_profiles.id"))
    pre_tension_score: Mapped[float] = mapped_column(Float) # 0.0 to 1.0
    payload_vector: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=True) # 768-dim embedding
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    context_tags: Mapped[list[str]] = mapped_column(ARRAY(String))
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
