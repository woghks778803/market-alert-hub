from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, Index, BINARY, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base

class UserOauthAccount(Base):
    __tablename__ = "user_oauth_accounts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 1:0..1 관계 보장
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                         nullable=False, unique=True)

    provider_id: Mapped[int] = mapped_column(ForeignKey("oauth_providers.id"),
                                             nullable=False)

    # ========== 옵션 A: 평문 식별자 ==========
    provider_user_id: Mapped[str] = mapped_column(String(128), nullable=False)

    # ========== 옵션 B: 지문(비가역) ==========
    # provider_user_fp: Mapped[bytes] = mapped_column(BINARY(32), nullable=False)

    linked_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, nullable=False)
    unlinked_at: Mapped[datetime | None] = mapped_column(DateTime())

    __table_args__ = (
        # A안: (provider_id, provider_user_id) 유니크
        UniqueConstraint("provider_id", "provider_user_id", name="uq_oauth_provider_uid"),
        # B안 사용 시 위 대신:
        # UniqueConstraint("provider_id", "provider_user_fp", name="uq_oauth_provider_uid"),

        Index("ix_oauth_user_id", "user_id"),
    )
