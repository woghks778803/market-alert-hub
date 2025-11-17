from datetime import datetime
from sqlalchemy import Text, Integer, DateTime, ForeignKey, Enum as SAEnum, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base
from app.core.constants import DeliveryStatus
from app.core.util.datetime import utcnow

class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    alert_event_id: Mapped[int] = mapped_column(ForeignKey("alert_events.id", ondelete="CASCADE"), nullable=False, index=True)
    user_channel_id: Mapped[int] = mapped_column(ForeignKey("user_channels.id", ondelete="RESTRICT"), nullable=False, index=True)

    status: Mapped[DeliveryStatus] = mapped_column(
        SAEnum(DeliveryStatus, native_enum=True, create_constraint=True, validate_strings=True), 
        default=DeliveryStatus.QUEUED, server_default=DeliveryStatus.QUEUED, nullable=False
    )
    sent_at:       Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_code: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        server_default=func.now(), 
        default=utcnow, 
        nullable=False
    )

    __table_args__ = (Index("ix_deliveries_status", "status"),)
