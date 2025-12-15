from datetime import datetime
from sqlalchemy import Integer, String, Boolean, JSON, DateTime, ForeignKey, func, text, BINARY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base
from app.core.util.datetime import utcnow

class UserChannel(Base):
    __tablename__ = "user_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_provider_id: Mapped[int] = mapped_column(
        ForeignKey("channel_providers.id", ondelete="RESTRICT"),
        nullable=False, index=True
    )

    address:      Mapped[str | None] = mapped_column(String(255))
    config:       Mapped[dict | None] = mapped_column(JSON)
    config_fingerprint: Mapped[bytes | None] = mapped_column(BINARY(32), index=True)
    verified_at:  Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=utcnow, 
        onupdate=utcnow, 
        nullable=False
    )
    is_default:   Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))
    is_deleted:   Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))

    targets: Mapped[list["AlertChannelTarget"]] = relationship(back_populates="user_channel", cascade="all, delete-orphan")
    channel_provider: Mapped["ChannelProvider"] = relationship("ChannelProvider", back_populates="channels")
