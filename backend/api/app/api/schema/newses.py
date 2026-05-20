from datetime import datetime
from decimal import Decimal

from app.core.constants import LanguageCode, TranslationCode
from app.api.schema.base import ApiResponseModel


class PostRead(ApiResponseModel):
    news_item_id: int
    title_original: str
    description_original: str | None
    guid: str | None
    link: str
    published_at: datetime
    fetched_at: datetime

    translation_id: int
    translation_local: LanguageCode
    translation_provider: TranslationCode | None
    title: str | None
    description: str | None
    translated_at: datetime

    click_count: int
    share_count: int

    item_language: LanguageCode
    provider_language: LanguageCode
    provider_name: str