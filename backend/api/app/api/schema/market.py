from datetime import datetime
from decimal import Decimal
from pydantic import AwareDatetime

from app.core.constants import CandleBaseInterval, AssetType
from app.api.schema.base import ApiResponseModel, ApiRequestModel


class BackfillRequestIn(ApiRequestModel):
    exchange_instrument_ids: list[int]
    base: CandleBaseInterval
    start_at: AwareDatetime
    end_at: AwareDatetime
    reason: str


class SimpleOk(ApiResponseModel):
    ok: bool = True


class ExchangeSimpleRead(ApiResponseModel):
    id: int
    code: str
    name: str


class ExchangeDetailRead(ApiResponseModel):
    id: int
    code: str
    name: str
    name_ko: str | None
    country: str | None
    timezone: str
    base_url: str | None
    market_count: int


class InstrumentDetailRead(ApiResponseModel):
    id: int
    symbol: str
    name: str
    name_ko: str | None
    asset_type: AssetType
    exchange_count: int
    market_count: int


class MarketSimpleRead(ApiResponseModel):
    exchange_instrument_id: int
    exchange_symbol: str
    exchange_name: str
    base_symbol: str
    quote_symbol: str


class MarketRead(ApiResponseModel):
    exchange_instrument_id: int
    exchange_symbol: str
    exchange_code: str
    exchange_name: str
    base_name: str
    base_name_ko: str
    base_symbol: str
    quote_symbol: str

    is_watchlisted: bool

    # Pydantic Decimal은 JSON으로 나갈 때 기본적으로 string으로 직렬화된다
    open_price: Decimal | None
    close_price: Decimal | None
    price_change_24h: Decimal | None
    price_change_rate_24h: Decimal | None

    normalized_price: Decimal | None
    normalized_volume: Decimal | None

    high_24h: Decimal | None
    low_24h: Decimal | None
    volume_24h: Decimal | None


class CandleRead(ApiResponseModel):
    exchange_instrument_id: int
    ts_open: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = 0.0


# class CandleIngestResult(BaseModel):
#     id: int
#     created: bool  # True=insert, False=update(when upsert)
