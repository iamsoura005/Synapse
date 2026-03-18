import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from app.database.postgres import Base
from sqlalchemy import Enum as SQLEnum
import enum

class ContractStatus(str, enum.Enum):
    active = "active"
    archived = "archived"
    renegotiating = "renegotiating"
    expired = "expired"

class LivingContract(Base):
    __tablename__ = "living_contracts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    negotiation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("negotiations.id"))
    party_ids: Mapped[list[str]] = mapped_column(ARRAY(String))
    clauses: Mapped[list[dict]] = mapped_column(JSONB) # List of Clause objects JSON
    status: Mapped[ContractStatus] = mapped_column(SQLEnum(ContractStatus), default=ContractStatus.active)
    polygon_hash: Mapped[str] = mapped_column(String, nullable=True)
    polygon_tx_hash: Mapped[str] = mapped_column(String, nullable=True)
    polygon_scan_url: Mapped[str] = mapped_column(String, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_contract_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("living_contracts.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
