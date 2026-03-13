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
    market_id: int
    symbol: str
    exchange_code: str
    base_asset: str
    quote_asset: str
    asset_name: str
    volume: Decimal | None
    price: Decimal | None
    change_rate: Decimal | None
    is_watchlisted: bool


class MappingItem(BaseModel):
    exchange_id: int
    base_asset_id: int
    quote_asset_id: int


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
