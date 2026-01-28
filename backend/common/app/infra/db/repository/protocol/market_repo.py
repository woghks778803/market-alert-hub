from typing import Protocol, Sequence, Tuple
from datetime import datetime
from app.domain import MarketDTO


class MarketRepo(Protocol):
    def add_exchange_instruments(
        self, exchange_instruments: list[MarketDTO.ExchangeInstrumentCreate]
    ) -> None: ...
    def get_exchange_by_filter(
        self,
        id: int | None = None,
        code: str | None = None,
        is_active: bool = True,
        is_delete: bool = False,
    ) -> MarketDTO.Exchange | None: ...
    def get_last_1m_by_exchange_instrument_ids(
        self,
        exchange_instrument_ids: list[int],
    ) -> dict[int, MarketDTO.PriceSnapshot]: ...
    def get_by_exchange_instrument_filter(
        self,
        *,
        exchange_instrument_id: int,
        is_active: bool = True,
        is_delete: bool = False,
    ) -> MarketDTO.ExchangeInstrument | None: ...
    def list_exchange_by_filter(
        self,
        *,
        is_active: bool = True,
        is_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[MarketDTO.Exchange]: ...
    def list_instrument_by_filter(
        self,
        *,
        is_active: bool | None = None,
        is_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[MarketDTO.Instrument]: ...
    def list_exchange_instrument_by_filter(
        self,
        *,
        exchange_id: int | None = None,
        is_active: bool | None = None,
        is_deleted: bool = False,
        limit: int = 200,
        offset: int = 0,
    ) -> list[MarketDTO.MappingItem]: ...
    def list_mappings_exchange_id(
        self, *, exchange_id: int | None = None
    ) -> list[MarketDTO.MappingItem]: ...
    def _list_candle_by_filter(
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
    def upsert_exchange_instruments_by_pairs(
        self,
        exchange_id: int,
        pairs: list[tuple[int, int]],
        is_active: bool,
        updated_at: datetime,
    ) -> int: ...
    def upsert_snapshot_1m(
        self, row: MarketDTO.PriceSnapshotCreate
    ) -> Tuple[int, bool]: ...
    def upsert_snapshot_1h(
        self, row: MarketDTO.PriceSnapshotCreate
    ) -> Tuple[int, bool]: ...
    def upsert_snapshot_1d(
        self, row: MarketDTO.PriceSnapshotCreate
    ) -> Tuple[int, bool]: ...
    def _upsert_snapshot(
        self, model, row: MarketDTO.PriceSnapshotCreate
    ) -> Tuple[int, bool]: ...

    def upsert_snapshots_1m(
        self,
        rows: list[MarketDTO.PriceSnapshotCreate],
        *,
        chunk_size: int = 1000,
    ) -> None: ...

    def seed_snapshots(self, *, interval: str, chunk: list): ...

    def get_symbol(self, exchange_instrument_id: int) -> MarketDTO.MappingItem: ...
