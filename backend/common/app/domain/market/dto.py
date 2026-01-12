from typing import NamedTuple
from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal
from app.core.constants import AssetType


@dataclass(slots=True, frozen=True)
class CandleBase:
    exchange_instrument_id: int
    ts_open: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(slots=True)
class MappingItem:
    id: int | None = None

    exchange_id: int | None = None
    exchange_name: str | None = None
    exchange_symbol: str | None = None
    base_asset_id: int | None = None
    base_symbol: str | None = None
    quote_asset_id: int | None = None
    quote_symbol: str | None = None


@dataclass(slots=True)
class ExchangeInstrument:
    id: int
    exchange_id: int
    base_asset_id: int
    quote_asset_id: int
    exchange_symbol: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    is_active: bool
    price_precision: int | None
    qty_precision: int | None
    min_notional: Decimal | None


@dataclass(slots=True)
class ExchangeInstrumentCreate:
    id: int


@dataclass(slots=True)
class Exchange:
    id: int
    code: str
    name: str
    timezone: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    is_active: bool
    country: str | None
    base_url: str | None


@dataclass(slots=True)
class Instrument:
    id: int
    symbol: str
    asset_type: AssetType
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    is_active: bool


@dataclass(slots=True)
class PriceSnapshot:
    id: int
    exchange_instrument_id: int
    ts_open: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ParsedMarketSymbol:
    quote: str
    base: str


@dataclass(frozen=True)
class SymbolInfo:
    symbol: str  # 예: "KRW-BTC"
    name_kr: str
    name_en: str
