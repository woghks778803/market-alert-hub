from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.core.constants import LanguageCode, TranslationCode

_model_cfg = ConfigDict(from_attributes=True, use_enum_values=True)

class PostRead(BaseModel):
    model_config = _model_cfg

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