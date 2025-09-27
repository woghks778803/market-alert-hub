from datetime import datetime
from pydantic import BaseModel, ConfigDict

_model = ConfigDict(from_attributes=True, use_enum_values=True)

class MarketInstrumentItem(BaseModel):
    id: int
    exchange_symbol: str
    base_symbol: str
    quote_symbol: str
    exchange_name: str

    model_config = _model

class ExchangeRead(BaseModel):
    model_config = _model
    id: int
    code: str
    name: str

class InstrumentRead(BaseModel):
    model_config = _model
    id: int
    code: str
    name: str

class MappingItem(BaseModel):
    exchange_id: int
    base_asset_id: int
    quote_asset_id: int

class CandleRead(BaseModel):
    model_config = _model
    exchange_id: int
    instrument_id: int
    ts_open: datetime 
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None

class ExchangeInstrumentListItem(BaseModel):
    id: int
    exchange_symbol: str
    base_symbol: str
    exchange_name: str

