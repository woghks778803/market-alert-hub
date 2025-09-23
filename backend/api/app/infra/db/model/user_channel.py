from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import String, Boolean, JSON, DateTime, ForeignKey, Index, Enum as SAEnum, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base
from app.core.datetime_utils import utcnow

class UserChannel(Base):
    __tablename__ = "user_channels"

    class ChannelType(str, enum.Enum):
        email = "email"; webhook = "webhook"; telegram = "telegram"; slack = "slack"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_type: Mapped[ChannelType] = mapped_column(
        SAEnum(ChannelType, native_enum=True, create_constraint=True, validate_strings=True),
        default=ChannelType.email, server_default=ChannelType.email, nullable=False
    )
    address:      Mapped[str | None] = mapped_column(String(255))
    config:       Mapped[dict | None] = mapped_column(JSON)
    verified_at:  Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_default:   Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        server_default=func.now(), 
        default=utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        server_default=func.now(), 
        default=utcnow, 
        onupdate=utcnow, 
        nullable=False
    )
    is_valid:   Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("1"))

    targets: Mapped[list["AlertChannelTarget"]] = relationship(back_populates="user_channel", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_user_channels_type", "channel_type"),)
