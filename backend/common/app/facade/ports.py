from typing import Any, Mapping, Protocol

JsonDict = dict[str, Any]


class ActiveMarketCatalog(Protocol):
    async def get_exchanges_snap(self) -> Mapping[str, JsonDict]:
        raise NotImplementedError

    async def get_exchanges_meta(self) -> Mapping[str, str]:
        raise NotImplementedError

    async def get_symbols_snap(self, exchange_code: str) -> Mapping[str, JsonDict]:
        raise NotImplementedError

    async def get_symbols_meta(self, exchange_code: str) -> Mapping[str, str]:
        raise NotImplementedError


class CandleStore(Protocol):
    async def write_1s(self, state: dict) -> None:
        raise NotImplementedError

    async def get_1s(self, exchange: str, symbol: str) -> dict | None:
        raise NotImplementedError

    async def subscribe_1s(self, type: str):
        raise NotImplementedError
