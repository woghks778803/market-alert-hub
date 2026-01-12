from typing import Protocol
from .dto import SymbolInfo

class UpbitSymbolProvider(Protocol):
    def list_symbols(self) -> list[SymbolInfo]: ...
