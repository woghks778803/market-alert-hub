from typing import Any, Mapping, NamedTuple
from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal
from app.core.constants import AssetType
from app.domain.shared.errors import ValidationAppError


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
    id: int
    base_asset_id: int
    quote_asset_id: int

    exchange_id: int | None = None
    exchange_name: str | None = None
    exchange_symbol: str | None = None
    base_symbol: str | None = None
    quote_symbol: str | None = None

    @staticmethod
    def _req_int(d: Mapping[str, Any], key: str) -> int:
        v = d.get(key)
        if v is None:
            raise ValidationAppError(f"MappingItem.{key} is required")
        try:
            return int(v)
        except Exception as e:
            raise ValidationAppError(
                f"MappingItem.{key} must be int-like: {v!r}"
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
                f"MappingItem.{key} must be int-like: {v!r}"
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
    def from_dict(cls, d: Mapping[str, Any]) -> "MappingItem":
        return cls(
            id=cls._req_int(d, "id"),
            base_asset_id=cls._req_int(d, "base_asset_id"),
            quote_asset_id=cls._req_int(d, "quote_asset_id"),
            exchange_id=cls._opt_int(d, "exchange_id"),
            exchange_name=cls._opt_str(d, "exchange_name"),
            exchange_symbol=cls._opt_str(d, "exchange_symbol"),
            base_symbol=cls._opt_str(d, "base_symbol"),
            quote_symbol=cls._opt_str(d, "quote_symbol"),
        )


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
    exchange_id: int
    base_asset_id: int
    quote_asset_id: int
    exchange_symbol: str
    updated_at: datetime
    is_deleted: bool
    is_active: bool
    price_precision: int | None = None
    qty_precision: int | None = None
    min_notional: Decimal | None = None


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
    name_kr: str
    name_en: str
