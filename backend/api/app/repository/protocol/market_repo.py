from typing import Iterable, Sequence
from app.infra.db.model import Exchange, Instrument, PriceLatest, PriceSnapshot1m
from datetime import datetime

class MarketRepo:

    def list_exchanges(self, *, limit: int = 100, offset: int = 0) -> Sequence[Exchange]: ...
    def list_instruments(self, *, exchange_id: int | None = None, limit: int = 200, offset: int = 0) -> Sequence[Instrument]: ...
    def list_mapping(self, *, exchange_id: int | None = None) -> Iterable[tuple[int, int]]: ...
    def get_latest(self, *, exchange_id: int, instrument_id: int) -> PriceLatest | None: ...
    def list_candles_1m(
        self, *,
        exchange_id: int,
        instrument_id: int,
        start: datetime | None,
        end: datetime | None,
        limit: int = 500,
        asc_order: bool = True,
    ) -> Sequence[PriceSnapshot1m]:
        ...
