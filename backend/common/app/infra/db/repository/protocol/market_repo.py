from typing import Protocol, Sequence, Tuple
from datetime import datetime
from app.domain import MarketDTO


class MarketRepo(Protocol):
    def get_exchange_by_filter(
        self,
        id: int | None = None,
        code: str | None = None,
        is_active: bool = True,
        is_delete: bool = False,
    ) -> MarketDTO.Exchange | None: ...
    def get_by_exchange_instrument_filter(
        self,
        *,
        exchange_instrument_id: int,
        is_active: bool = True,
        is_delete: bool = False,
    ) -> MarketDTO.ExchangeInstrument | None: ...
    def list_exchanges_by_filter(
        self,
        *,
        is_active: bool = True,
        is_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[MarketDTO.Exchange]: ...
    def list_instruments_by_filter(
        self,
        *,
        is_active: bool = True,
        is_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[MarketDTO.Instrument]: ...
    def list_exchange_instruments_by_filter(
        self,
        *,
        exchange_id: int | None = None,
        is_deleted: bool = False,
        limit: int = 200,
        offset: int = 0,
    ) -> list[MarketDTO.MappingItem]: ...
    def list_mappings_exchange_id(
        self, *, exchange_id: int | None = None
    ) -> list[MarketDTO.MappingItem]: ...
    def _list_candles_by_filter(
        self,
        model,
        *,
        exchange_instrument_id: int,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        asc_order: bool,
    ) -> Sequence: ...
    def list_1m_by_filter(
        self,
        *,
        exchange_instrument_id: int,
        cursor: datetime | None,
        start: datetime | None,
        end: datetime | None,
        limit: int | None,
        asc_order: bool,
    ) -> list[MarketDTO.CandleBase]: ...
    def list_1h_by_filter(
        self,
        *,
        exchange_instrument_id: int,
        cursor: datetime | None,
        start: datetime | None,
        end: datetime | None,
        limit: int | None,
        asc_order: bool,
    ) -> list[MarketDTO.CandleBase]: ...
    def list_1d_by_filter(
        self,
        *,
        exchange_instrument_id: int,
        cursor: datetime | None,
        start: datetime | None,
        end: datetime | None,
        limit: int | None,
        asc_order: bool,
    ) -> list[MarketDTO.CandleBase]: ...

    def upsert_1m(self, row: dict) -> Tuple[int, bool]: ...
    def upsert_1h(self, row: dict) -> Tuple[int, bool]: ...
    def upsert_1d(self, row: dict) -> Tuple[int, bool]: ...
    def _upsert_one_mysql(self, model, row: dict) -> Tuple[int, bool]: ...

    def seed_snapshots(self, *, interval: str, chunk: list): ...

    def get_symbols(self, exchange_instrument_id: int) -> MarketDTO.MappingItem: ...
