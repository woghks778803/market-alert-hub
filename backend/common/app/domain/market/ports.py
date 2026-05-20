from typing import Any, Mapping, Protocol
from .dto import SymbolInfo

JsonDict = dict[str, Any]

class ExchangeSymbol(Protocol):
    def list_symbols(self) -> list[SymbolInfo]:
        raise NotImplementedError


class MarketSnapshot(Protocol):
    def candle_publish(self, payloads: list, interval_type: str) -> None:
        raise NotImplementedError

    def ticker_publish(self, payloads: list, interval_type: str) -> None:
        raise NotImplementedError


class CandleStore(Protocol):
    def get_1s(self, exchange: str, symbol: str) -> dict | None:
        raise NotImplementedError


class AsyncMarketCatalog(Protocol):
    async def get_exchanges_snap(self) -> Mapping[str, JsonDict]:
        raise NotImplementedError

    async def get_exchanges_meta(self) -> Mapping[str, str]:
        raise NotImplementedError

    async def get_symbols_snap(self, exchange_code: str) -> Mapping[str, JsonDict]:
        raise NotImplementedError

    async def get_symbols_meta(self, exchange_code: str) -> Mapping[str, str]:
        raise NotImplementedError


class AsyncCandleStore(Protocol):
    async def write_1s(self, state: dict) -> None:
        raise NotImplementedError

    async def get_1s(self, exchange: str, symbol: str) -> dict | None:
        raise NotImplementedError

    async def subscribe(self, type: str):
        raise NotImplementedError


class AsyncTickerStore(Protocol):
    async def subscribe(self, type: str):
        raise NotImplementedError