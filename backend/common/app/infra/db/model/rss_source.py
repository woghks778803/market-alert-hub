from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.util.datetime import utcnow
from app.domain import NewsDTO
from app.infra.db.base import Base


class RssSource(Base):
    __tablename__ = "rss_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    rss_provider_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rss_providers.id"),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    feed_url: Mapped[str] = mapped_column(String(500), nullable=False)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )

    etag: Mapped[str | None] = mapped_column(String(255))
    last_modified: Mapped[str | None] = mapped_column(String(255))

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
        Index("ix_rss_source_provider", "rss_provider_id"),
        Index("ix_rss_source_active", "is_active"),
        Index("ix_rss_source_provider_code", "rss_provider_id", "code"),
    )

    def to_dto(self) -> NewsDTO.RssSource:
        return NewsDTO.RssSource(
            id=self.id,
            rss_provider_id=self.rss_provider_id,
            code=self.code,
            name=self.name,
            feed_url=self.feed_url,
            is_active=self.is_active,
            etag=self.etag,
            last_modified=self.last_modified,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
        )