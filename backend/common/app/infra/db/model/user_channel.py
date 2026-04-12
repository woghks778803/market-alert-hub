from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, func, text, BINARY, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base
from app.core.util.datetime import utcnow
from app.domain import ChannelDTO

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
    config_hash: Mapped[bytes | None] = mapped_column(BINARY(32), nullable=True, index=True)
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
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    is_active:  Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))

    targets: Mapped[list["AlertChannelTarget"]] = relationship(back_populates="user_channel", cascade="all, delete-orphan")
    channel_provider: Mapped["ChannelProvider"] = relationship("ChannelProvider", back_populates="channels")

    __table_args__ = (
        UniqueConstraint(
            "channel_provider_id",
            "user_id",
            "address",
            name="uq_user_channel_provider_user_address"
        ),
        Index(
            "ix_user_channel_address_provider",
            "channel_provider_id",
            "address",
        ),
        Index(
            "ix_user_channel_user_provider",
            "user_id",
            "channel_provider_id",
        ),
    )

    def to_dto(self) -> ChannelDTO.UserChannel:
        return ChannelDTO.UserChannel(
            id=self.id,
            user_id=self.user_id,
            channel_provider_id=self.channel_provider_id,
            address=self.address,
            config=self.config,
            config_hash=self.config_hash,
            verified_at=self.verified_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
            is_active=self.is_active,
        )

    @classmethod
    def from_create_dto(cls, dto: ChannelDTO.UserChannelCreate) -> "UserChannel":
        return cls(
            user_id=dto.user_id,
            channel_provider_id=dto.channel_provider_id,
            address=dto.address,
            config=dto.config,
            config_hash=dto.config_hash,
            verified_at=dto.verified_at,
            is_active=dto.is_active,
            # 생성 기본값
            deleted_at=None,
        )