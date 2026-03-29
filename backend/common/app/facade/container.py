from typing import Callable
from functools import cached_property

from app.facade.ports import TickerStore, CandleStore, ActiveMarketCatalog


class FacadeContainer:
    def __init__(
        self,
        candle_store: Callable[[], CandleStore],
        ticker_store: Callable[[], TickerStore],
        active_catalog: Callable[[], ActiveMarketCatalog],
    ) -> None:
        self._candle_store = candle_store
        self._ticker_store = ticker_store
        self._active_catalog = active_catalog

    @cached_property
    def candle_store(self):
        return self._candle_store()

    @cached_property
    def ticker_store(self):
        return self._ticker_store()

    @cached_property
    def active_catalog(self):
        return self._active_catalog()
