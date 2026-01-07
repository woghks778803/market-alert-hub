from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, UniqueConstraint, Index, BINARY, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base
from app.domain import UserDTO

class UserOauthAccount(Base):
    __tablename__ = "user_oauth_accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 1:0..1 관계 보장
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                         nullable=False, unique=True)

    oauth_providers_id: Mapped[int] = mapped_column(ForeignKey("oauth_providers.id"),
                                             nullable=False)

    provider_user_id: Mapped[str] = mapped_column(String(128), nullable=False)

    linked_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, nullable=False)
    unlinked_at: Mapped[datetime | None] = mapped_column(DateTime())

    __table_args__ = (
        # A안: (oauth_providers_id, provider_user_id) 유니크
        UniqueConstraint("oauth_providers_id", "provider_user_id", name="uq_oauth_provider_uid"),

        Index("ix_oauth_user_id", "user_id"),
    )

    def to_dto(self) -> UserDTO.UserOAuthAccount:
        return UserDTO.UserOAuthAccount(
            id=self.id,
            user_id=self.user_id,
            oauth_providers_id=self.oauth_providers_id,
            provider_user_id=self.provider_user_id,
            linked_at=self.linked_at,
            unlinked_at=self.unlinked_at,
        )