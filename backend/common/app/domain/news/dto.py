from dataclasses import dataclass
from datetime import datetime
from app.core.constants import LanguageCode, NewsItemStatus, NewsItemTranslationStatus

@dataclass(frozen=True)
class ParsedNewsFeedItem:
    guid: str | None
    link: str | None
    title: str | None
    description: str | None
    content: str | None
    author: str | None
    image_url: str | None
    published_at: datetime | None

@dataclass(frozen=True)
class NewsFeedFetchRequest:
    feed_url: str
    timeout_sec: float
    etag: str | None = None
    last_modified: str | None = None


@dataclass(frozen=True)
class NewsFeedFetchResult:
    not_modified: bool
    etag: str | None
    last_modified: str | None
    items: list[ParsedNewsFeedItem]

@dataclass(frozen=True)
class TranslateTextItem:
    ref_id: int
    text: str


@dataclass(frozen=True)
class TranslateBatchRequest:
    source_language: str
    target_language: str
    items: list[TranslateTextItem]


@dataclass(frozen=True)
class TranslatedTextItem:
    ref_id: int
    original_text: str
    translated_text: str


@dataclass(frozen=True)
class TranslateBatchResult:
    items: list[TranslatedTextItem]

@dataclass(frozen=True)
class RssProvider:
    id: int
    code: str
    name: str
    description: str | None
    homepage_url: str | None
    language: LanguageCode
    is_active: bool
    request_timeout_sec: int
    rate_limit_policy: dict | None
    retry_policy: dict | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

@dataclass(frozen=True)
class RssSource:
    id: int
    rss_provider_id: int
    code: str
    name: str
    feed_url: str
    is_active: bool
    etag: str | None
    last_modified: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

@dataclass(frozen=True)
class NewsItem:
    id: int
    rss_source_id: int

    guid: str | None
    link: str
    canonical_link: str | None

    title_original: str
    description_original: str | None
    content_original: str | None

    image_url: str | None
    author: str | None
    language: LanguageCode

    published_at: datetime | None
    fetched_at: datetime

    title_hash: str
    link_hash: str
    content_hash: str | None

    status: NewsItemStatus

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

@dataclass(frozen=True)
class NewsItemStat:
    news_item_id: int
    click_count: int
    share_count: int
    last_clicked_at: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

@dataclass(frozen=True)
class NewsItemTranslation:
    id: int
    news_item_id: int
    locale: LanguageCode

    title: str | None
    description: str | None

    provider: str | None
    status: NewsItemTranslationStatus

    requested_at: datetime | None
    translated_at: datetime | None
    failed_at: datetime | None

    error_code: str | None
    error_message: str | None

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None