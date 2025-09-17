from fastapi import APIRouter, Depends
from time import time
from app.api.schema.market import Ticker, TickerQuery
from app.core.market_registry import registry
from app.core.market_types import MarketAdapter
from app.domain import ValidationAppError
from typing import cast

router = APIRouter(prefix="/markets", tags=["markets"])

@router.get("/ticker", response_model=list[Ticker])
def get_ticker(q: TickerQuery = Depends()):
    adapter = registry.get(q.exchange)
    if not adapter:
        raise ValidationAppError(message="unsupported exchange", target="exchange")

    adapter = cast(MarketAdapter, adapter)
    symbols = [s.strip().upper() for s in q.symbols.split(",") if s.strip()]
    prices = adapter.ticker(symbols)
    now = int(time())

    return [
        Ticker(exchange=q.exchange, symbol=s, price=prices[s],
               price_24h_change_pct=None, ts=now)
        for s in symbols if prices.get(s) is not None
    ]
