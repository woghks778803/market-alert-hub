from .market_types import MarketAdapter

class MarketRegistry:
    def __init__(self): self._adapters: dict[str, object] = {}
    def register(self, adapter: MarketAdapter): self._adapters[adapter.id] = adapter
    def get(self, ex: str): return self._adapters.get(ex)          # ← 추가
    def has(self, ex: str) -> bool: return ex in self._adapters
    def list(self) -> list[str]: return list(self._adapters.keys())

registry = MarketRegistry()
