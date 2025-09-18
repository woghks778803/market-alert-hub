from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import DateTime, String, Integer, JSON, ForeignKey, Enum as SAEnum, UniqueConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base

class AlertStatus(str, enum.Enum):
    active   = "active"
    paused   = "paused"
    archived = "archived"

class AlertType(str, enum.Enum):
    price_above = "price_above"
    price_below = "price_below"
    pct_change_window = "pct_change_window"
    cross_exchange_spread = "cross_exchange_spread"
    volume_above = "volume_above"
    moving_avg_cross = "moving_avg_cross"

class AlertScope(str, enum.Enum):
    single = "single"
    cross  = "cross"

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id:       Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name:          Mapped[str] = mapped_column(String(100), nullable=False)

    status: Mapped[AlertStatus] = mapped_column(
        SAEnum(AlertStatus, native_enum=False, create_constraint=True, validate_strings=True), 
        default=AlertStatus.active, nullable=False, 
    )
    type: Mapped[AlertType] = mapped_column(
        SAEnum(AlertType, native_enum=False, create_constraint=True, validate_strings=True), 
        default=AlertType.price_above, nullable=False
    )
    scope: Mapped[AlertScope] = mapped_column(
        SAEnum(AlertScope, native_enum=False, create_constraint=True, validate_strings=True), 
        default=AlertScope.single, nullable=False
    )

    exchange_id:   Mapped[int] | None = mapped_column(ForeignKey("exchanges.id",  ondelete="RESTRICT"), index=True)
    instrument_id: Mapped[int] | None = mapped_column(ForeignKey("instruments.id", ondelete="RESTRICT"), index=True)

    params:            Mapped[dict] = mapped_column(JSON, nullable=False)
    throttle_seconds:  Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    valid_from:        Mapped[datetime] | None = mapped_column(DateTime(timezone=True))
    valid_to:          Mapped[datetime] | None = mapped_column(DateTime(timezone=True))
    timezone:          Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    last_fired_at:     Mapped[datetime] | None = mapped_column(DateTime(timezone=True))
    created_at:        Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:        Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    channels: Mapped[list["AlertChannelTarget"]] = relationship(back_populates="alert", cascade="all, delete-orphan")
    events:   Mapped[list["AlertEvent"]]         = relationship(back_populates="alert", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_alerts_user_name"),
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_type", "type"),
    )
