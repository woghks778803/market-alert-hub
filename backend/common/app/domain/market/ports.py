from typing import Protocol
from .dto import SymbolInfo


class UpbitSymbol(Protocol):
    def list_symbols(self) -> list[SymbolInfo]: ...
