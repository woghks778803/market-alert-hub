from typing import Iterable, Sequence
from datetime import datetime
from app.infra.db.model import (
    ExchangeModel, InstrumentModel,
    PriceSnapshot1mModel, PriceSnapshot1hModel, PriceSnapshot1dModel
)    
from app.domain.dto import market as MarketDTO

from decimal import Decimal

class MarketRepo:

    def list_exchanges(self, *, limit: int = 100, offset: int = 0) -> Sequence[ExchangeModel]: ...
    def list_exchange_instruments(self, *, exchange_id: int | None = None, limit: int = 200, offset: int = 0) -> list[MarketDTO.MarketInstrumentBrief]: ...
    def list_mapping(self, *, exchange_id: int | None = None) -> Iterable[tuple[int, int, int]]: ...
    def _list_candles(
        self,
        model,
        *,
        exchange_instrument_id: int,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        asc_order: bool,
    ) -> Sequence:
        ...
    def list_candles_1m(
        self, *, exchange_instrument_id: int,
        start: datetime | None, end: datetime | None,
        limit: int, asc_order: bool,
    ): ...
    def list_candles_1h(
        self, *, exchange_instrument_id: int,
        start: datetime | None, end: datetime | None,
        limit: int, asc_order: bool,
    ): ...
    def list_candles_1d(
        self, *, exchange_instrument_id: int,
        start: datetime | None, end: datetime | None,
        limit: int, asc_order: bool,
    ): ...

    def seed_snapshot(
        self,
        *,
        interval: str,
        exchange_instrument_id: int,
        ts_open: datetime,
        open: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: Decimal,
    ): ...

