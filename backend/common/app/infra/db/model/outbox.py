from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum as SAEnum, JSON, Index, BINARY
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base 
from app.core.util.datetime import utcnow
from app.core.constants import OutboxStatus
from app.domain import OutboxDTO

class Outbox(Base):
    __tablename__ = "outboxs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id: Mapped[str] = mapped_column(String(36), nullable=False)  # ix_outbox_trace
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(50), nullable=False)
    aggregate_id: Mapped[int] = mapped_column(Integer, nullable=False)
    outbox_fingerprint: Mapped[bytes | None] = mapped_column(BINARY(32), nullable=True, unique=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False) 
    
    status: Mapped[OutboxStatus] = mapped_column(
                                        SAEnum(OutboxStatus, name="outbox_status", values_callable=lambda e: [m.value for m in e],
                                        native_enum=True, create_constraint=True, validate_strings=True),
                                        nullable=False, default=OutboxStatus.PENDING, server_default=OutboxStatus.PENDING.value)
    
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
    

    def to_dto(self) -> OutboxDTO.Outbox:
        """
        ORM Model -> domain DTO (조회/반환용)
        """
        return OutboxDTO.Outbox(
            id=self.id,
            trace_id=self.trace_id,
            event_type=self.event_type,
            aggregate_type=self.aggregate_type,
            aggregate_id=self.aggregate_id,
            outbox_fingerprint=self.outbox_fingerprint,
            payload=self.payload,
            status=self.status,
            attempts=self.attempts,
            next_run_at=self.next_run_at,
            last_attempted_at=self.last_attempted_at,
            sent_at=self.sent_at,
            final_failed_at=self.final_failed_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_create_dto(cls, dto: OutboxDTO.OutboxCreate) -> "Outbox":
        """
        domain DTO -> ORM Model
        """
        return cls(
            trace_id=dto.trace_id,
            event_type=dto.event_type,
            aggregate_type=dto.aggregate_type,
            aggregate_id=dto.aggregate_id,
            outbox_fingerprint=dto.outbox_fingerprint,
            payload=dto.payload,
            status=dto.status,
            attempts=dto.attempts,
        )