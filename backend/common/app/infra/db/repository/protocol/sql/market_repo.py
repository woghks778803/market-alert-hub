from typing import Any, Protocol, Sequence, Tuple
from datetime import datetime
from app.core.constants import MarketSort, BackfillRequestItemStatus
from app.domain import MarketDTO


class MarketRepo(Protocol):
    def list_backfill_job_by_filter(
        self,
        *,
        backfill_request_id: int,
        statuses: list[BackfillRequestItemStatus] | None = None,
        limit: int,
    ) -> list[MarketDTO.MarketBackfillJob]: ...
    def list_ticker_stats_from_snapshots(
        self, is_active: bool, deleted_is_null: bool = True
    ) -> list[MarketDTO.ExchangeInstrumentTickerCreate]: ...
    def get_by_filter(
        self,
        user_id: int,
        exchange_instrument_id: int | None = None,
        exchange_code: str | None = None,
        exchange_symbol: str | None = None,
        is_active: bool = True,
        deleted_is_null: bool = True,
    ) -> MarketDTO.Market | None: ...
    def get_exchange_by_filter(
        self,
        exchange_id: int | None = None,
        exchange_code: str | None = None,
        is_active: bool = True,
        deleted_is_null: bool = True,
    ) -> MarketDTO.Exchange | None: ...
    def get_exchange_detail(
        self,
        *,
        exchange_code: str,
    ) -> MarketDTO.ExchangeDetail | None: ...
    def get_instrument_detail(
        self,
        *,
        instrument_symbol: str,
    ) -> MarketDTO.InstrumentDetail | None: ...
    def get_exchange_instrument_by_filter(
        self,
        *,
        exchange_instrument_id: int,
        is_active: bool = True,
        deleted_is_null: bool = True,
    ) -> MarketDTO.ExchangeInstrument | None: ...
    def get_last_1m_by_exchange_instrument_ids(
        self,
        exchange_instrument_ids: list[int],
    ) -> dict[int, MarketDTO.PriceSnapshot]: ...
    def list_exchange_by_filter(
        self,
        *,
        is_active: bool = True,
        deleted_is_null: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[MarketDTO.Exchange]: ...
    def list_by_filter(
        self,
        *,
        user_id: int,
        exchange_codes: list[str] | None,
        instrument_symbol: str | None = None,
        search: str | None,
        watchlist_only: bool,
        sort: MarketSort,
        is_active: bool | None = None,
        limit: int,
        offset: int,
    ) -> Sequence[MarketDTO.Market]: ...
    def list_instrument_by_filter(
        self,
        *,
        is_active: bool | None = None,
        deleted_is_null: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[MarketDTO.Instrument]: ...
    def list_exchange_instrument_by_filter(
        self,
        *,
        search: str | None = None,
        exchange_instrument_ids: set[int] | None = None,
        exchange_id: int | None = None,
        is_active: bool | None = None,
        deleted_is_null: bool = True,
        limit: int = 200,
        offset: int = 0,
    ) -> list[MarketDTO.MarketSimple]: ...
    def _list_snapshot_by_filter(
        self,
        model,
        *,
        exchange_instrument_id: int,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        asc_order: bool,
    ) -> Sequence: ...
    def list_snapshot_1m_by_filter(
        self,
        *,
        exchange_instrument_id: int,
        cursor: datetime | None,
        start: datetime | None,
        end: datetime | None,
        limit: int | None,
        asc_order: bool,
    ) -> list[MarketDTO.MarketCandle]: ...
    def list_snapshot_1h_by_filter(
        self,
        *,
        exchange_instrument_id: int,
        cursor: datetime | None,
        start: datetime | None,
        end: datetime | None,
        limit: int | None,
        asc_order: bool,
    ) -> list[MarketDTO.MarketCandle]: ...
    def list_snapshot_1d_by_filter(
        self,
        *,
        exchange_instrument_id: int,
        cursor: datetime | None,
        start: datetime | None,
        end: datetime | None,
        limit: int | None,
        asc_order: bool,
    ) -> list[MarketDTO.MarketCandle]: ...

    def list_snapshot_1h_agg(
        self,
        start_dt: datetime,
        end_dt: datetime,
    ) -> list[MarketDTO.PriceSnapshotCreate]: ...
    def list_snapshot_1d_agg(
        self,
        start_dt: datetime,
        end_dt: datetime,
    ) -> list[MarketDTO.PriceSnapshotCreate]: ...
    def add_backfile_request(
        self,
        row: MarketDTO.BackfillRequestCreate
    ) -> MarketDTO.BackfillRequest: ...
    def add_backfill_request_items(
        self,
        rows: list[MarketDTO.BackfillRequestItemCreate],
        *,
        chunk_size: int = 1000,
    ) -> None: ...
    def update_backfill_request_item(
        self,
        *,
        backfill_request_item_id: int,
        from_status: MarketDTO.BackfillRequestItemStatus,
        to_status: MarketDTO.BackfillRequestItemStatus,
        cursor_at: datetime | None = None,
        result_code: str | None = None,
        result_message: str | None = None,
        result_payload: dict[str, Any] | None = None,
    ) -> bool: ...
    def update_backfill_request_item_status(
        self,
        *,
        backfill_request_item_id: int,
        from_statuses: list[MarketDTO.BackfillRequestItemStatus],
        to_status: MarketDTO.BackfillRequestItemStatus,
    ) -> bool: ...
    def upsert_exchange_instrument_tickers(
        self,
        rows: list[MarketDTO.ExchangeInstrumentTickerCreate],
        *,
        chunk_size: int = 1000,
    ) -> int: ...
    def upsert_exchange_instruments(
        self, 
        rows: list[MarketDTO.ExchangeInstrumentSync],
        *,
        chunk_size: int = 1000,
    ) -> None: ...
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
    def upsert_snapshots_1h(
        self,
        rows: list[MarketDTO.PriceSnapshotCreate],
        *,
        chunk_size: int = 1000,
    ) -> None: ...

    def upsert_snapshots_1d(
        self,
        rows: list[MarketDTO.PriceSnapshotCreate],
        *,
        chunk_size: int = 1000,
    ) -> None: ...

    def seed_snapshots(self, *, interval: str, chunk: list): ...
