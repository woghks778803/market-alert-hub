from typing import Protocol, Iterable, Sequence, Tuple
from datetime import datetime
from app.infra.db.model import ExchangeModel, ExchangeInstrumentModel
from app.domain.market import dto as MarketDTO

class MarketRepo(Protocol):

    def get_by_exchange_instrument_id(self, *, exchange_instrumen_id: int) -> ExchangeInstrumentModel: ...
    def list_exchanges(self, *, limit: int = 100, offset: int = 0) -> Sequence[ExchangeModel]: ...
    def list_exchange_instruments(self, *, exchange_id: int | None = None, limit: int = 200, offset: int = 0) -> list[MarketDTO.MarketInstrumentItem]: ...
    def list_mapping(self, *, exchange_id: int | None = None) -> list[ExchangeInstrumentModel]: ...
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
        cursor: datetime | None, start: datetime | None, end: datetime | None,
        limit: int, asc_order: bool,
    ) -> list[MarketDTO.CandleBase]: ...
    def list_candles_1h(
        self, *, exchange_instrument_id: int,
        cursor: datetime | None, start: datetime | None, end: datetime | None,
        limit: int, asc_order: bool,
    ) -> list[MarketDTO.CandleBase]: ...
    def list_candles_1d(
        self, *, exchange_instrument_id: int,
        cursor: datetime | None, start: datetime | None, end: datetime | None,
        limit: int, asc_order: bool,
    ) -> list[MarketDTO.CandleBase]: ...

    def upsert_one_1m(self, row: dict) -> Tuple[int, bool]: ...
    def upsert_one_1h(self, row: dict) -> Tuple[int, bool]: ...
    def upsert_one_1d(self, row: dict) -> Tuple[int, bool]: ...
    def _upsert_one_mysql(self, model, row: dict) -> Tuple[int, bool]: ...
    
    def seed_snapshots(
        self,
        *,
        interval: str,
        chunk: list
    ): ...

    def get_symbols(self, exchange_instrument_id: int) -> MarketDTO.MappingSymbol: ...

