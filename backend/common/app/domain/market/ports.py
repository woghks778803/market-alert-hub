from typing import Protocol
from app.core.constants import CandleInterval
from .dto import SymbolInfo


class ExchangeSymbol(Protocol):
    def list_symbols(self) -> list[SymbolInfo]: ...


class MarketSnapshotPublish(Protocol):
    def candle_publish(self, payloads: list, type: str) -> None: ...

    def ticker_publish(self, payloads: list, type: str) -> None: ...
