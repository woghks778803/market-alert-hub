from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime, Enum as SAEnum, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base 
from app.core.datetime_utils import utcnow
from app.core.constants import OutboxStatus

class Outbox(Base):
    __tablename__ = "outboxs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trace_id: Mapped[str] = mapped_column(String(36), nullable=False)  # ix_outbox_trace
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    aggregate_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    dedupe_key: Mapped[str | None] = mapped_column(String(256), nullable=True, unique=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False) 
    
    status: Mapped[OutboxStatus] = mapped_column(
                                        SAEnum(OutboxStatus, name="outbox_status", values_callable=lambda e: [m.value for m in e],
                                        native_enum=True, create_constraint=True, validate_strings=True),
                                        nullable=False, default=OutboxStatus.PENDING, server_default=OutboxStatus.PENDING)
    
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    final_failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_outbox_status_next", "status", "next_run_at"),
        Index("ix_outbox_agg", "aggregate_type", "aggregate_id"),
    )
