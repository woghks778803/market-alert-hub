from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

_model_cfg = ConfigDict(from_attributes=True, use_enum_values=True)


class WatchlistCreate(BaseModel):
    exchange_instrument_id: int = Field(..., ge=1)
    sort_order: int | None = Field(None, ge=0)


class WatchlistItemRead(BaseModel):
    model_config = _model_cfg
    id: int
    exchange_instrument_id: int
    sort_order: int
