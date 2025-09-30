from typing import NamedTuple
from datetime import datetime
from dataclasses import dataclass

class MappingItem(NamedTuple):
    exchange_id: int
    base_asset_id: int
    quote_asset_id: int

class MappingSymbol(NamedTuple):
    exchange_symbol: str
    base_symbol: str
    quote_symbol: str

@dataclass(slots=True, frozen=True)
class MarketInstrumentItem:
    id: int
    exchange_symbol: str
    base_symbol: str
    quote_symbol: str
    exchange_name: str

@dataclass(slots=True, frozen=True)
class CandleBase:
    exchange_instrument_id: int
    ts_open: datetime 
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass(slots=True, frozen=True)
class ExchangeInstrumentListItem:
    id: int
    exchange_symbol: str
    base_symbol: str
    exchange_name: str