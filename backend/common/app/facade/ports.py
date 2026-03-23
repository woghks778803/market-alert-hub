from typing import Any, Mapping, Protocol

JsonDict = dict[str, Any]


class ActiveMarketCatalog(Protocol):
    async def get_exchanges_snap(self, key_prefix: str) -> Mapping[str, JsonDict]: ...

    async def get_exchanges_meta(self, key_prefix: str) -> Mapping[str, str]: ...

    async def get_symbols_snap(
        self, key_prefix: str, exchange_code: str
    ) -> Mapping[str, JsonDict]: ...

    async def get_symbols_meta(
        self, key_prefix: str, exchange_code: str
    ) -> Mapping[str, str]: ...


class CandleStore(Protocol):
    async def write_1s(self, state: dict) -> None:
        raise NotImplementedError

    async def get_1s(self, exchange: str, symbol: str) -> dict | None:
        raise NotImplementedError
