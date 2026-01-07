from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, DateTime, JSON, Index, text
from app.infra.db.base import Base
from app.domain import ChannelDTO

class ChannelProvider(Base):
    __tablename__ = "channel_providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    user_schema: Mapped[dict | None] = mapped_column(JSON)     # optional
    admin_schema: Mapped[dict | None] = mapped_column(JSON)    # optional
    rate_limit_policy: Mapped[dict | None] = mapped_column(JSON)
    retry_policy: Mapped[dict | None] = mapped_column(JSON)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("0"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    channels: Mapped[list["UserChannel"]] = relationship("UserChannel", back_populates="channel_provider")

    __table_args__ = (Index("ix_channel_providers_active", "is_active"),)


    def to_dto(self) -> ChannelDTO.ChannelProvider:
        return ChannelDTO.ChannelProvider(
            id=self.id,
            code=self.code,
            name=self.name,
            description=self.description,
            user_schema=self.user_schema,
            admin_schema=self.admin_schema,
            rate_limit_policy=self.rate_limit_policy,
            retry_policy=self.retry_policy,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )