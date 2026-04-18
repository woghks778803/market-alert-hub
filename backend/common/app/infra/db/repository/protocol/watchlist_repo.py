from typing import Protocol
from app.domain import WatchlistDTO


class WatchlistRepo(Protocol):
    def add_item(
        self, *, user_id: int, exchange_instrument_id: int, sort_order: int
    ) -> WatchlistDTO.WatchlistItem: ...
    def get_item_by_filter(
        self, *, user_id: int, exchange_instrument_id: int
    ) -> WatchlistDTO.WatchlistItem | None: ...

    def get_next_sort(self, *, user_id: int) -> int: ...

    def delete_item(self, *, user_id: int, exchange_instrument_id: int) -> None: ...
