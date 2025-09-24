from datetime import datetime
from pydantic import BaseModel, ConfigDict

_model = ConfigDict(from_attributes=True, use_enum_values=True)

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
    instrument_id: int

class LatestPriceRead(BaseModel):
    model_config = _model
    exchange_id: int
    instrument_id: int
    price: float
    as_of: datetime

class Candle1mRead(BaseModel):
    model_config = _model
    exchange_id: int
    instrument_id: int
    bucket: datetime   # 1분 버킷 (UTC)
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
