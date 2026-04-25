from datetime import datetime
from decimal import Decimal
from sqlalchemy import DECIMAL, DateTime, String, JSON, ForeignKey, Index, Integer, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.util.datetime import utcnow
from app.core.constants import AlertEventStatus
from app.domain import AlertDTO
from app.infra.db.base import Base

class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    alert_id: Mapped[int] = mapped_column(
        ForeignKey("alerts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    exchange_instrument_id: Mapped[int | None] = mapped_column(
        ForeignKey("exchange_instruments.id", ondelete="RESTRICT"),
        index=True,
    )

    status: Mapped[AlertEventStatus] = mapped_column(
        SAEnum(
            AlertEventStatus, values_callable=lambda e: [m.value for m in e], 
            native_enum=True, create_constraint=True, validate_strings=True
        ),
        default=AlertEventStatus.PENDING,
        server_default=AlertEventStatus.PENDING,
        nullable=False,
    )

    detected_at:   Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    queued_at:   Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    trigger_value: Mapped[Decimal | None] = mapped_column(DECIMAL(32, 16))
    context:       Mapped[dict | None] = mapped_column(JSON)

    dedup_key:     Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=utcnow, 
        nullable=False
    )

    alert: Mapped["Alert"] = relationship(back_populates="events")

    __table_args__ = (
        Index("ix_alert_events_alert_detected", "alert_id", "detected_at"),
        Index("ix_alert_events_status_detected", "status", "detected_at"),
    )

    def to_dto(self) -> AlertDTO.AlertEvent:
        return AlertDTO.AlertEvent(
            id=self.id,
            alert_id=self.alert_id,
            exchange_instrument_id=self.exchange_instrument_id,
            status=self.status,
            detected_at=self.detected_at,
            queued_at=self.queued_at,
            trigger_value=self.trigger_value,
            context=self.context,
            dedup_key=self.dedup_key,
            created_at=self.created_at,
        )

    @classmethod
    def from_create_dto(cls, dto: AlertDTO.AlertEventCreate) -> "AlertEvent":
        return cls(
            alert_id=dto.alert_id,
            exchange_instrument_id=dto.exchange_instrument_id,
            detected_at=dto.detected_at,
            trigger_value=dto.trigger_value,
            context=dto.context,
            dedup_key=dto.dedup_key,
        )