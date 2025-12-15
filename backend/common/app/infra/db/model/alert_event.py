from datetime import datetime
from decimal import Decimal
from sqlalchemy import DECIMAL, DateTime, String, JSON, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base
from app.core.util.datetime import utcnow

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

    detected_at:   Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    trigger_value: Mapped[Decimal | None] = mapped_column(DECIMAL(32, 16))
    context:       Mapped[dict | None] = mapped_column(JSON)

    dedup_key:     Mapped[str | None] = mapped_column(String(64), unique=True)  # DDL 길이에 맞춰 조정
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=utcnow, 
        nullable=False
    )

    alert: Mapped["Alert"] = relationship(back_populates="events")

    __table_args__ = (
        Index("ix_alert_events_alert_detected", "alert_id", "detected_at"),
    )
