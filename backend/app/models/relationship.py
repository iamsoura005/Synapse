import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database.postgres import Base
from sqlalchemy import Enum as SQLEnum
import enum

class RelationshipType(str, enum.Enum):
    friend = "friend"
    colleague = "colleague"
    roommate = "roommate"
    client = "client"
    family = "family"
    other = "other"

class NegotiationStyle(str, enum.Enum):
    collaborative = "collaborative"
    competitive = "competitive"
    avoidant = "avoidant"
    accommodating = "accommodating"

class RelationshipProfile(Base):
    __tablename__ = "relationship_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String, index=True) # Could FK to users.id but keeping as str for flexibility with external auth
    counterparty_id: Mapped[str] = mapped_column(String)
    relationship_type: Mapped[RelationshipType] = mapped_column(SQLEnum(RelationshipType))
    health_score: Mapped[float] = mapped_column(Float, default=70.0) # 0-100
    trust_index: Mapped[float] = mapped_column(Float, default=0.5) # 0-1
    compatibility_score: Mapped[float] = mapped_column(Float, default=0.5) # 0-1
    negotiation_style: Mapped[NegotiationStyle] = mapped_column(SQLEnum(NegotiationStyle), default=NegotiationStyle.collaborative)
    last_negotiation_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    total_negotiations: Mapped[int] = mapped_column(Integer, default=0)
    successful_resolutions: Mapped[int] = mapped_column(Integer, default=0)
