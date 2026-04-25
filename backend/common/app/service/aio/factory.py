from typing import Callable
from functools import cached_property

from app.core import dto as CoreDTO
from app.domain.shared.async_uow import AsyncUnitOfWork
from app.domain import MarketPort, AlertPort, ThrottlePort

from .alert_service import AlertService

class AsyncServiceFactory:
    def __init__(
        self,
        *,
        uow: Callable[[], AsyncUnitOfWork],
        candle_store: Callable[[], MarketPort.AsyncCandleStore],
        ticker_store: Callable[[], MarketPort.AsyncTickerStore],
        active_catalog: Callable[[], MarketPort.AsyncMarketCatalog],
        alert_snapshot: Callable[[], AlertPort.AsyncAlertSnapshot],
        alert_bucket: Callable[[], AlertPort.AsyncAlertBucket],
        alert_event: Callable[[], AlertPort.AsyncAlertEvent],
        cooldown: Callable[[], ThrottlePort.AsyncCooldown],
    ) -> None:
        self._uow = uow
        self._candle_store = candle_store
        self._ticker_store = ticker_store
        self._active_catalog = active_catalog
        self._alert_snapshot = alert_snapshot
        self._alert_bucket = alert_bucket
        self._alert_event = alert_event
        self._cooldown = cooldown

    @property
    def uow(self) -> Callable[[], AsyncUnitOfWork]:
        return self._uow

    @cached_property
    def candle_store(self):
        return self._candle_store()

    @cached_property
    def ticker_store(self):
        return self._ticker_store()

    @cached_property
    def active_catalog(self):
        return self._active_catalog()

    @cached_property
    def alert_snapshot(self):
        return self._alert_snapshot()
    
    @cached_property
    def alert_bucket(self):
        return self._alert_bucket()

    @cached_property
    def alert_event(self):
        return self._alert_event()

    @cached_property
    def cooldown(self):
        return self._cooldown()

    @cached_property
    def alerts(self) -> AlertService:
        return AlertService(
            uow_factory=self._uow,
            alert_event=self.alert_event,
        )