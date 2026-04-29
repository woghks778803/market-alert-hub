from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import TranslationCode, LanguageCode, NewsItemTranslationStatus
from app.core.util.datetime import utcnow
from app.domain import NewsDTO
from app.infra.db.base import Base


class NewsItemTranslation(Base):
    __tablename__ = "news_item_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    news_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("news_items.id"),
        nullable=False,
    )

    locale: Mapped[LanguageCode] = mapped_column(
        SAEnum(
            LanguageCode, values_callable=lambda e: [m.value for m in e], 
            native_enum=True, create_constraint=True, validate_strings=True
        ),
        nullable=False,
        default=LanguageCode.KO,
        server_default=LanguageCode.KO.value,
    )

    title: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)

    provider: Mapped[TranslationCode | None] = mapped_column(
        SAEnum(
            TranslationCode, values_callable=lambda e: [m.value for m in e], 
            native_enum=True, create_constraint=True, validate_strings=True
        ),
        default=None,
        server_default=None,
    )

    status: Mapped[NewsItemTranslationStatus] = mapped_column(
        SAEnum(
            NewsItemTranslationStatus, values_callable=lambda e: [m.value for m in e], 
            native_enum=True, create_constraint=True, validate_strings=True
        ),
        nullable=False,
        default=NewsItemTranslationStatus.PENDING,
        server_default=NewsItemTranslationStatus.PENDING.value,
    )

    requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    translated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)

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
        Index(
            "ix_news_item_translation_item_locale",
            "news_item_id",
            "locale",
            unique=True,
        ),
        Index(
            "ix_news_item_translation_status_locale",
            "status",
            "locale",
        ),
    )

    def to_dto(self) -> NewsDTO.NewsItemTranslation:
        return NewsDTO.NewsItemTranslation(
            id=self.id,
            news_item_id=self.news_item_id,
            locale=self.locale,
            title=self.title,
            description=self.description,
            provider=self.provider,
            status=self.status,
            requested_at=self.requested_at,
            translated_at=self.translated_at,
            failed_at=self.failed_at,
            error_code=self.error_code,
            error_message=self.error_message,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
        )