from typing import Protocol, Sequence
from datetime import datetime

from app.core.constants import (
    TranslationCode, 
    LanguageCode, 
    NewsPostsort,
    NewsItemTranslationStatus, 
    NewsItemStatus
)
from app.domain import NewsDTO

class NewsRepo(Protocol):
    def list_news_item_translation_by_filter(
        self,
        *,
        rss_source_id: int,
        locale: LanguageCode,
        translation_status: NewsItemTranslationStatus,
        item_status: NewsItemStatus,
    ) -> list[NewsDTO.NewsItemTranslationTarget]: ...

    def list_news_item_by_link_fingerprints(
        self,
        *,
        rss_source_id: int,
        link_fingerprints: list[bytes],
    ) -> list[NewsDTO.NewsItem]: ...

    def list_news_feed_by_filter(
        self,
        *,
        is_active: bool = True,
        deleted_is_null: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[NewsDTO.NewsFeed]: ...

    def list_news_post_by_filter(
        self,
        *,
        locale: LanguageCode,
        translation_status: NewsItemTranslationStatus,
        item_status: NewsItemStatus,
        search: str | None,
        cursor_at: datetime | None,
        cursor_id: int | None,
        start: datetime | None,
        end: datetime | None,
        limit: int = 100,
        sort: NewsPostsort | None,
        deleted_is_null: bool = True,
    ) -> Sequence[NewsDTO.NewsPost]: ...

    def get_news_feed_by_id(
        self,
        rss_source_id: int,
        is_active: bool = True,
        deleted_is_null: bool = True,
    ) -> NewsDTO.NewsFeed | None: ...

    def add_news_item_stats(
        self,
        rows: list[NewsDTO.NewsItemTranslationCreate],
        *,
        chunk_size: int = 1000,
    ) -> int: ...
    
    def add_news_item_translations(
        self,
        rows: list[NewsDTO.NewsItemTranslationCreate],
        *,
        chunk_size: int = 1000,
    ) -> int: ...

    def upsert_news_items(
        self,
        rows: list[NewsDTO.NewsItemCreate],
        *,
        chunk_size: int = 1000,
    ) -> int: ...

    def update_rss_source(
        self,
        *,
        rss_source_id: int,
        etag: str | None,
        last_modified: str | None,
        deleted_is_null: bool = True,
    ) -> None:  ...

    def update_news_item_translations(
        self,
        *,
        ids: list[int],
        status: NewsItemTranslationStatus,
        provider: TranslationCode | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        requested_at: datetime | None = None,
        failed_at: datetime | None = None,
        deleted_is_null: bool = True,
    ) -> None: ...

    def update_news_item_translations_done(
        self,
        *,
        rows: list[NewsDTO.NewsItemTranslationDone],
        status: NewsItemTranslationStatus,
        translated_at: datetime,
        deleted_is_null: bool = True,
    ) -> None: ...