from pydantic import BaseModel, field_validator
from app.core.market_registry import registry


class Ticker(BaseModel):
    exchange: str
    symbol: str
    price: float
    price_24h_change_pct: float | None = None
    ts: int

class TickerQuery(BaseModel):
    exchange: str
    symbols: str

    @field_validator("exchange")
    def _check_exchange(cls, v):
        if not registry.has(v):
            from app.domain import ValidationAppError
            raise ValidationAppError(message="unsupported exchange", target="exchange")
        return v