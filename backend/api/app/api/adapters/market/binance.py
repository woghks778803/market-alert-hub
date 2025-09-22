from app.core.market_registry import registry

class BinanceAdapter:
    id = "binance"
    _price = {"BTC": 62345.0, "ETH": 2450.0}

    def ticker(self, symbols: list[str]): return {s: self._price.get(s) for s in symbols}
    
registry.register(BinanceAdapter())
