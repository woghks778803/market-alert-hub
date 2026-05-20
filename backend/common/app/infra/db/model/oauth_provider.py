from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

from app.core.util.datetime import utcnow
from app.domain import UserDTO
from app.infra.db.base import Base


class OauthProvider(Base):
    __tablename__ = "oauth_providers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(
        String(16), unique=True, nullable=False
    )  # 'kakao', 'google'...
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    def to_dto(self) -> UserDTO.OauthProvider:
        return UserDTO.OauthProvider(
            id=self.id,
            code=self.code,
            display_name=self.display_name,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
