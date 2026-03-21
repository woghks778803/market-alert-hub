from typing import Protocol


class CandleStore(Protocol):
    async def write_1s(self, state: dict) -> None:
        raise NotImplementedError

    async def get_1s(self, exchange: str, symbol: str) -> dict | None:
        raise NotImplementedError
