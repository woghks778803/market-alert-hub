from datetime import datetime

from sqlalchemy import BINARY, DateTime, ForeignKey, Index, Integer, String, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.util.datetime import utcnow
from app.core.constants import LanguageCode, NewsItemStatus
from app.domain import NewsDTO
from app.infra.db.base import Base


class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    rss_source_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rss_sources.id"),
        nullable=False,
    )

    guid: Mapped[str | None] = mapped_column(String(500))
    link: Mapped[str] = mapped_column(String(1000), nullable=False)
    canonical_link: Mapped[str | None] = mapped_column(String(1000))

    title_original: Mapped[str] = mapped_column(String(500), nullable=False)
    description_original: Mapped[str | None] = mapped_column(Text)
    content_original: Mapped[str | None] = mapped_column(Text)

    image_url: Mapped[str | None] = mapped_column(String(1000))
    author: Mapped[str | None] = mapped_column(String(255))

    language: Mapped[LanguageCode] = mapped_column(
        SAEnum(
            LanguageCode, values_callable=lambda e: [m.value for m in e], 
            native_enum=True, create_constraint=True, validate_strings=True
        ),
        nullable=False,
        default=LanguageCode.UNKNOWN,
        server_default=LanguageCode.UNKNOWN.value,
    )

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    title_fingerprint: Mapped[bytes] = mapped_column(BINARY(32), nullable=False)
    link_fingerprint: Mapped[bytes] = mapped_column(BINARY(32), nullable=False)
    content_fingerprint: Mapped[bytes | None] = mapped_column(BINARY(32))

    status: Mapped[NewsItemStatus] = mapped_column(
        SAEnum(
            NewsItemStatus, values_callable=lambda e: [m.value for m in e], 
            native_enum=True, create_constraint=True, validate_strings=True
        ),
        nullable=False,
        default=NewsItemStatus.ACTIVE,
        server_default=NewsItemStatus.ACTIVE.value,
    )

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
        Index("ix_news_item_source", "rss_source_id"),
        Index("ix_news_item_status_published", "status", "published_at"),
        Index("ix_news_item_published", "published_at"),
        Index("ix_news_item_source_guid", "rss_source_id", "guid", unique=True),
        Index("ix_news_item_source_link_fp", "rss_source_id", "link_fingerprint", unique=True),
        Index("ix_news_item_source_title_fp", "rss_source_id", "title_fingerprint"),
    )

    def to_dto(self) -> NewsDTO.NewsItem:
        return NewsDTO.NewsItem(
            id=self.id,
            rss_source_id=self.rss_source_id,
            guid=self.guid,
            link=self.link,
            canonical_link=self.canonical_link,
            title_original=self.title_original,
            description_original=self.description_original,
            content_original=self.content_original,
            image_url=self.image_url,
            author=self.author,
            language=self.language,
            published_at=self.published_at,
            fetched_at=self.fetched_at,
            title_fingerprint=self.title_fingerprint,
            link_fingerprint=self.link_fingerprint,
            content_fingerprint=self.content_fingerprint,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
        )