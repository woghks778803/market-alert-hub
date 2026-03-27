from typing import Protocol
from .dto import SymbolInfo


class ExchangeSymbol(Protocol):
    def list_symbols(self) -> list[SymbolInfo]:
        raise NotImplementedError


class MarketSnapshotPublish(Protocol):
    def candle_publish(self, payloads: list, type: str) -> None:
        raise NotImplementedError

    def ticker_publish(self, payloads: list, type: str) -> None:
        raise NotImplementedError


class CandleStore(Protocol):
    def get_1s(self, exchange: str, symbol: str) -> dict | None:
        raise NotImplementedError
