from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime, Enum as SAEnum, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base 
from app.core.datetime_utils import utcnow
from app.core.constants import OutboxStatus

class Outbox(Base):
    __tablename__ = "outboxs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False) 
    
    status: Mapped[OutboxStatus] = mapped_column(
                                        SAEnum(OutboxStatus, name="outbox_status", values_callable=lambda e: [m.value for m in e],
                                        native_enum=True, create_constraint=True, validate_strings=True),
                                        nullable=False, default=OutboxStatus.PENDING, server_default=OutboxStatus.PENDING)
    
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
