from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, func, BINARY
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base
from app.core.util.datetime import utcnow
from app.domain import UserDTO


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[bytes] = mapped_column(
        BINARY(32), nullable=False, unique=True
    )  # DDL 길이에 맞게 조정

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    def to_dto(self) -> UserDTO.PasswordReset:
        return UserDTO.PasswordReset(
            id=self.id,
            user_id=self.user_id,
            token_hash=self.token_hash,
            expires_at=self.expires_at,
            sent_at=self.sent_at,
            consumed_at=self.consumed_at,
            created_at=self.created_at,
        )

    @classmethod
    def from_create_dto(cls, dto: UserDTO.PasswordResetCreate) -> "PasswordReset":
        return cls(
            user_id=dto.user_id,
            token_hash=dto.token_hash,
            expires_at=dto.expires_at,
        )
