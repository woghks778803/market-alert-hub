from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, JSON, String, text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import LanguageCode
from app.core.util.datetime import utcnow
from app.domain import NewsDTO
from app.infra.db.base import Base

class RssProvider(Base):
    __tablename__ = "rss_providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    homepage_url: Mapped[str | None] = mapped_column(String(500))
    language: Mapped[LanguageCode] = mapped_column(
        SAEnum(
            LanguageCode, values_callable=lambda e: [m.value for m in e], 
            native_enum=True, create_constraint=True, validate_strings=True
        ),
        default=LanguageCode.EN,
        server_default=LanguageCode.EN.value,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )

    request_timeout_sec: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
        server_default=text("10"),
    )

    rate_limit_policy: Mapped[dict | None] = mapped_column(JSON)
    retry_policy: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_rss_provider_active", "is_active"),
    )

    def to_dto(self) -> NewsDTO.RssProvider:
        return NewsDTO.RssProvider(
            id=self.id,
            code=self.code,
            name=self.name,
            description=self.description,
            homepage_url=self.homepage_url,
            language=self.language,
            is_active=self.is_active,
            request_timeout_sec=self.request_timeout_sec,
            rate_limit_policy=self.rate_limit_policy,
            retry_policy=self.retry_policy,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
        )