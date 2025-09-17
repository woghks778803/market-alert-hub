from typing import Protocol, Mapping

class MarketAdapter(Protocol):
    id: str
    def ticker(self, symbols: list[str]) -> Mapping[str, float | None]: ...