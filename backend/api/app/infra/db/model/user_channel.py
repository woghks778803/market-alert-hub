from datetime import datetime
from sqlalchemy import String, Boolean, JSON, DateTime, ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base
from app.core.datetime_utils import utcnow

class UserChannel(Base):
    __tablename__ = "user_channels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_provider_id: Mapped[int] = mapped_column(
        ForeignKey("channel_providers.id", ondelete="RESTRICT"),
        nullable=False, index=True
    )

    address:      Mapped[str | None] = mapped_column(String(255))
    config:       Mapped[dict | None] = mapped_column(JSON)
    verified_at:  Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_default:   Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=utcnow, 
        onupdate=utcnow, 
        nullable=False
    )
    is_valid:   Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("1"))

    targets: Mapped[list["AlertChannelTarget"]] = relationship(back_populates="user_channel", cascade="all, delete-orphan")
    channel_provider: Mapped["ChannelProvider"] = relationship("ChannelProvider", back_populates="channels")
