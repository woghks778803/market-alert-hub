from app.core.market_registry import registry

class UpbitAdapter:
    id = "upbit"
    _price = {"BTC": 85123000.0, "ETH": 3200000.0}

    def ticker(self, symbols: list[str]): return {s: self._price.get(s) for s in symbols}

registry.register(UpbitAdapter())
