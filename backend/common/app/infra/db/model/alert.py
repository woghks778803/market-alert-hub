from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    String,
    Integer,
    JSON,
    ForeignKey,
    Enum as SAEnum,
    UniqueConstraint,
    Index,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.constants import AlertStatus
from app.core.util.datetime import utcnow
from app.domain import AlertDTO
from app.infra.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alert_type_id: Mapped[int] = mapped_column(
        ForeignKey("alert_types.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    exchange_instrument_id: Mapped[int | None] = mapped_column(
        ForeignKey("exchange_instruments.id", ondelete="RESTRICT"), index=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    status: Mapped[AlertStatus] = mapped_column(
        SAEnum(
            AlertStatus, values_callable=lambda e: [m.value for m in e], 
            native_enum=True, create_constraint=True, validate_strings=True
        ),
        default=AlertStatus.ACTIVE,
        server_default=AlertStatus.ACTIVE.value,
        nullable=False,
    )

    params: Mapped[dict] = mapped_column(JSON, nullable=False)
    throttle_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_fired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_once: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )

    channels: Mapped[list["AlertChannelTarget"]] = relationship(
        back_populates="alert", cascade="all, delete-orphan"
    )
    events: Mapped[list["AlertEvent"]] = relationship(
        back_populates="alert", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_alerts_status", "status"),
    )

    def to_dto(self) -> AlertDTO.Alert:
        return AlertDTO.Alert(
            id=self.id,
            user_id=self.user_id,
            alert_type_id=self.alert_type_id,
            exchange_instrument_id=self.exchange_instrument_id,
            name=self.name,
            timezone=self.timezone,
            status=self.status,
            
            params=self.params,

            is_once=self.is_once,
            throttle_seconds=self.throttle_seconds,
            
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            last_fired_at=self.last_fired_at,
            
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
        )


    @classmethod
    def from_create_dto(cls, dto: AlertDTO.AlertCreate) -> "Alert":
        return cls(
            user_id=dto.user_id,
            alert_type_id=dto.alert_type_id,
            exchange_instrument_id=dto.exchange_instrument_id,
            name=dto.name,
            timezone=dto.timezone,
            status=dto.status,
            
            params=dto.params,
            
            is_once=dto.is_once,
            throttle_seconds=dto.throttle_seconds,
            valid_from=dto.valid_from,
            valid_to=dto.valid_to,

            # 생성 기본값
            last_fired_at=None,
            deleted_at=None,
        )