class MarketStore:
    def __init__(self):
        self._candle_data = {}
        self._ticker_data = {}

    def get_candle_data(self):
        return self._candle_data

    def update_candle(self, key, value):
        self._candle_data[key] = value

    def candle_list_snapshot(self, interval):
        return [
            v for k, v in self._candle_data.items()
            if f":{interval}:" in k
        ]

    def candle_snapshot(self, key):
        return self._candle_data.get(key)

    def get_ticker_data(self):
        return self._ticker_data

    def update_ticker(self, key, value):
        self._ticker_data[key] = value

    def ticker_list_snapshot(self):
        return list(self._ticker_data.values())

    def ticker_snapshot(self, key):
        return self._ticker_data.get(key)
