from typing import Protocol, Sequence
from app.domain import WatchlistDTO
from app.infra.db.model import WatchlistItemModel


class WatchlistRepo(Protocol):
    def add_item(
        self, *, user_id: int, exchange_instrument_id: int, sort_order: int
    ) -> WatchlistDTO.WatchlistItem: ...
    def list_items_by_filter(
        self, *, user_id: int, limit: int, offset: int, is_asc: bool
    ) -> Sequence[WatchlistDTO.WatchlistItem]: ...
    def get_item_by_filter(
        self, *, user_id: int, exchange_instrument_id: int
    ) -> WatchlistDTO.WatchlistItem | None: ...

    def get_next_sort(self, *, user_id: int) -> int: ...

    def delete_item(self, *, user_id: int, exchange_instrument_id: int) -> None: ...
