from typing import Protocol
from app.core.constants import CandleInterval
from .dto import SymbolInfo


class ExchangeSymbol(Protocol):
    def list_symbols(self) -> list[SymbolInfo]: ...


class MarketSnapshotPublish(Protocol):
    def publish(self, payloads: list, type: str) -> None: ...
