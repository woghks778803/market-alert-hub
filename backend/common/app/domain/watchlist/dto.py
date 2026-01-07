from dataclasses import dataclass
from datetime import datetime

@dataclass(slots=True, frozen=True)
class WatchlistCreate:
    exchange_instrument_id: int
    sort_order: int | None

@dataclass(slots=True, frozen=True)
class WatchlistItemRead:
    id: int
    exchange_instrument_id: int
    base_symbol: str
    quote_symbol: str
    exchange_symbol: str
    sort_order: int
    created_at: datetime

@dataclass(slots=True)
class WatchlistItem:
    id: int
    user_id: int
    exchange_instrument_id: int
    note: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool