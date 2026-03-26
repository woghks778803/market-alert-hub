from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

_model_cfg = ConfigDict(from_attributes=True, use_enum_values=True)


class MarketInstrumentItem(BaseModel):
    id: int
    exchange_symbol: str
    base_symbol: str
    quote_symbol: str
    exchange_name: str

    model_config = _model_cfg


class ExchangeRead(BaseModel):
    model_config = _model_cfg
    id: int
    code: str
    name: str


class MarketRead(BaseModel):
    id: int
    symbol: str
    exchange_code: str
    base_asset: str
    quote_asset: str
    asset_name: str

    is_watchlisted: bool

    # Pydantic Decimal은 JSON으로 나갈 때 기본적으로 string으로 직렬화된다
    open_price: Decimal | None
    close_price: Decimal | None
    price_change_24h: Decimal | None
    price_change_rate_24h: Decimal | None

    high_24h: Decimal | None
    low_24h: Decimal | None
    volume_24h: Decimal | None


class CandleBase(BaseModel):
    model_config = _model_cfg
    exchange_instrument_id: int
    ts_open: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = 0.0


class ExchangeInstrumentListItem(BaseModel):
    id: int
    exchange_symbol: str
    base_symbol: str
    exchange_name: str


class CandleIngestResult(BaseModel):
    id: int
    created: bool  # True=insert, False=update(when upsert)
