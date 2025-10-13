from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, Integer, JSON, ForeignKey, Enum as SAEnum, UniqueConstraint, Index, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base
from app.core.constants import AlertStatus, AlertType, AlertScope
from app.core.datetime_utils import utcnow

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id:       Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name:          Mapped[str] = mapped_column(String(100), nullable=False)

    status: Mapped[AlertStatus] = mapped_column(
        SAEnum(AlertStatus, native_enum=True, create_constraint=True, validate_strings=True), 
        default=AlertStatus.ACTIVE, server_default=AlertStatus.ACTIVE, nullable=False, 
    )
    type: Mapped[AlertType] = mapped_column(
        SAEnum(AlertType, native_enum=True, create_constraint=True, validate_strings=True), 
        default=AlertType.PRICE_ABOVE, server_default=AlertType.PRICE_ABOVE, nullable=False
    )
    scope: Mapped[AlertScope] = mapped_column(
        SAEnum(AlertScope, native_enum=True, create_constraint=True, validate_strings=True), 
        default=AlertScope.SINGLE, server_default=AlertScope.SINGLE, nullable=False
    )

    exchange_instrument_id: Mapped[int | None] = mapped_column(
        ForeignKey("exchange_instruments.id", ondelete="RESTRICT"), index=True
    )

    params:            Mapped[dict] = mapped_column(JSON, nullable=False)
    throttle_seconds:  Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    valid_from:        Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_to:          Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    timezone:          Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    last_fired_at:     Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=utcnow, 
        onupdate=utcnow, 
        nullable=False
    )
    is_deleted:   Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))

    channels: Mapped[list["AlertChannelTarget"]] = relationship(back_populates="alert", cascade="all, delete-orphan")
    events:   Mapped[list["AlertEvent"]]         = relationship(back_populates="alert", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_alerts_user_name"),
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_type", "type"),
    )
