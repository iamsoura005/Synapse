import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, Boolean, Enum as SQLEnum, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.database.postgres import Base
import enum

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    agent_voice_id: Mapped[str] = mapped_column(String, nullable=True) # ElevenLabs voice ID
    emotion_readiness_score: Mapped[float] = mapped_column(Float, default=100.0)
    tension_threshold: Mapped[int] = mapped_column(Integer, default=65) # 0-100
    receptive_windows: Mapped[list[dict]] = mapped_column(JSONB, nullable=True) # [{start_hour, end_hour, days_of_week}]
    connected_integrations: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
