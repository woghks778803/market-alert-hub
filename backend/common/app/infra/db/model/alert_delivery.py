from datetime import datetime
from sqlalchemy import Text, Integer, DateTime, ForeignKey, Enum as SAEnum, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.constants import AlertDeliveryStatus
from app.core.util.datetime import utcnow
from app.domain import AlertDTO
from app.infra.db.base import Base


class AlertDelivery(Base):
    __tablename__ = "alert_deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    alert_event_id: Mapped[int] = mapped_column(ForeignKey("alert_events.id", ondelete="CASCADE"), nullable=False, index=True)
    user_channel_id: Mapped[int] = mapped_column(ForeignKey("user_channels.id", ondelete="RESTRICT"), nullable=False, index=True)

    status: Mapped[AlertDeliveryStatus] = mapped_column(
        SAEnum(
            AlertDeliveryStatus, 
            values_callable=lambda e: [m.value for m in e], 
            native_enum=True, create_constraint=True, validate_strings=True
        ), 
        default=AlertDeliveryStatus.QUEUED, 
        server_default=AlertDeliveryStatus.QUEUED, 
        nullable=False
    )
    sent_at:       Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_code: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (Index("ix_deliveries_status", "status"),)

    def to_dto(self) -> AlertDTO.AlertDelivery:
        return AlertDTO.AlertDelivery(
            id=self.id,
            alert_event_id=self.alert_event_id,
            user_channel_id=self.user_channel_id,
            status=self.status,
            sent_at=self.sent_at,
            response_code=self.response_code,
            response_body=self.response_body,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )