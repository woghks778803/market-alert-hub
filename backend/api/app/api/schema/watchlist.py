from datetime import datetime
from pydantic import Field

from app.api.schema.base import ApiResponseModel, ApiRequestModel


class WatchlistIn(ApiRequestModel):
    exchange_instrument_id: int = Field(..., ge=1)
    sort_order: int | None = Field(None, ge=0)


class WatchlistItemRead(ApiResponseModel):
    id: int
    exchange_instrument_id: int
    sort_order: int
