from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base

class UserIdentity(Base):
    __tablename__ = "user_identities"

    class ProviderType(str, enum.Enum):
        google = "google"; github = "github"; kakao = "kakao"; naver = "naver"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    provider_type: Mapped[ProviderType] = mapped_column(
        SAEnum(ProviderType, native_enum=True, create_constraint=True, validate_strings=True),
        default=ProviderType.kakao, server_default=ProviderType.kakao, nullable=False
    )
    provider_user_id:  Mapped[str] = mapped_column(String(128), nullable=False)

    access_token:  Mapped[str | None] = mapped_column(String(2048))
    refresh_token: Mapped[str | None] = mapped_column(String(2048))
    expires_at:    Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        server_default=func.now(), 
        default=func.now(), 
        nullable=False
    )

    __table_args__ = (UniqueConstraint("provider_type", "provider_user_id", name="uq_identity_provider_uid"),)
