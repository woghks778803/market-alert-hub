from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

_cfg = ConfigDict(from_attributes=True, use_enum_values=True)

class WatchlistCreate(BaseModel):
    exchange_instrument_id: int = Field(..., ge=1)
    sort_order: int | None = Field(None, ge=0)

class WatchlistItemRead(BaseModel):
    model_config = _cfg
    id: int
    exchange_instrument_id: int
    base_symbol: str
    quote_symbol: str
    exchange_symbol: str
    sort_order: int
    created_at: datetime
