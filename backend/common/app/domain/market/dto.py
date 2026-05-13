from typing import Any, Mapping, NamedTuple
from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal
from app.core.constants import AssetType
from app.domain.shared.errors import ValidationAppError


@dataclass(slots=True, frozen=True)
class MarketCandle:
    exchange_instrument_id: int
    ts_open: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(slots=True)
class MarketSimple:
    exchange_instrument_id: int
    base_asset_id: int
    quote_asset_id: int

    exchange_id: int | None = None
    exchange_name: str | None = None
    exchange_code: str | None = None
    exchange_symbol: str | None = None
    base_symbol: str | None = None
    quote_symbol: str | None = None

    @staticmethod
    def _req_int(d: Mapping[str, Any], key: str) -> int:
        v = d.get(key)
        if v is None:
            raise ValidationAppError(f"MarketSimple.{key} is required")
        try:
            return int(v)
        except Exception as e:
            raise ValidationAppError(
                f"MarketSimple.{key} must be int-like: {v!r}"
            ) from e

    @staticmethod
    def _opt_int(d: Mapping[str, Any], key: str) -> int | None:
        v = d.get(key)
        if v is None:
            return None
        try:
            return int(v)
        except Exception as e:
            raise ValidationAppError(
                f"MarketSimple.{key} must be int-like: {v!r}"
            ) from e

    @staticmethod
    def _opt_str(d: Mapping[str, Any], key: str) -> str | None:
        v = d.get(key)
        if v is None:
            return None
        if isinstance(v, bytes):
            s = v.decode("utf-8", errors="ignore")
        else:
            s = str(v)
        s = s.strip()
        return s or None

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "MarketSimple":
        return cls(
            exchange_instrument_id=cls._req_int(d, "exchange_instrument_id"),
            base_asset_id=cls._req_int(d, "base_asset_id"),
            quote_asset_id=cls._req_int(d, "quote_asset_id"),
            exchange_id=cls._opt_int(d, "exchange_id"),
            exchange_name=cls._opt_str(d, "exchange_name"),
            exchange_symbol=cls._opt_str(d, "exchange_symbol"),
            base_symbol=cls._opt_str(d, "base_symbol"),
            quote_symbol=cls._opt_str(d, "quote_symbol"),
        )


@dataclass(slots=True)
class Market:
    exchange_instrument_id: int
    exchange_symbol: str
    exchange_code: str
    exchange_name: str

    base_symbol: str
    quote_symbol: str
    asset_name: str

    open_price: Decimal | None
    close_price: Decimal | None
    price_change_24h: Decimal | None
    price_change_rate_24h: Decimal | None

    normalized_price: Decimal | None
    normalized_volume: Decimal | None

    high_24h: Decimal | None
    low_24h: Decimal | None
    volume_24h: Decimal | None

    is_watchlisted: bool


@dataclass(slots=True)
class ExchangeInstrumentTicker:
    id: int
    exchange_instrument_id: int
    open_price: Decimal
    close_price: Decimal
    high_24h: Decimal
    low_24h: Decimal
    volume_24h: Decimal
    price_change_24h: Decimal
    price_change_rate_24h: Decimal
    normalized_price: Decimal
    normalized_volume: Decimal
    updated_at: datetime


@dataclass(slots=True)
class ExchangeInstrumentTickerCreate:
    exchange_instrument_id: int
    open_price: Decimal
    close_price: Decimal
    high_24h: Decimal
    low_24h: Decimal
    volume_24h: Decimal
    price_change_24h: Decimal
    price_change_rate_24h: Decimal
    normalized_price: Decimal | None = None
    normalized_volume: Decimal | None = None


@dataclass(slots=True)
class ExchangeInstrument:
    id: int
    exchange_id: int
    base_asset_id: int
    quote_asset_id: int
    exchange_symbol: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    is_active: bool
    price_precision: int | None
    qty_precision: int | None
    min_notional: Decimal | None
    tick_size: Decimal | None


@dataclass(slots=True)
class ExchangeInstrumentSync:
    exchange_id: int
    base_asset_id: int
    quote_asset_id: int
    exchange_symbol: str
    updated_at: datetime
    is_active: bool
    
    price_precision: int | None = None
    qty_precision: int | None = None
    min_notional: Decimal | None = None
    tick_size: Decimal | None = None


@dataclass(slots=True)
class Exchange:
    id: int
    code: str
    name: str
    timezone: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    is_active: bool
    country: str | None
    base_url: str | None


@dataclass(slots=True)
class Instrument:
    id: int
    name: str
    symbol: str
    asset_type: AssetType
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
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


@dataclass(slots=True)
class PriceSnapshotCreate:
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
    base: str
    quote: str

    tick_size: Decimal | None = None
    price_precision: int | None = None
    qty_precision: int | None = None
    min_notional: Decimal | None = None
