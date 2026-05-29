import logging
from typing import Callable

from app.domain import MarketPort
from app.domain.shared.async_uow import AsyncUnitOfWork

logger = logging.getLogger(__name__)

class MarketService:
    def __init__(
        self,
        uow_factory: Callable[[], AsyncUnitOfWork],
        active_catalog: MarketPort.AsyncMarketCatalog,
        candle_store: MarketPort.AsyncCandleStore,
        ticker_store: MarketPort.AsyncTickerStore,
    ):
        self._uow_factory = uow_factory
        self._active_catalog = active_catalog
        self._candle_store = candle_store
        self._ticker_store = ticker_store

    async def get_candle_channels(
        self,
        interval_type: str,
    ) -> set[str]:
        return await self._build_channels(
            store=self._candle_store,
            interval_type=interval_type,
        )

    async def get_ticker_channels(
        self,
        interval_type: str,
    ) -> set[str]:
        return await self._build_channels(
            store=self._ticker_store,
            interval_type=interval_type,
        )

    async def _build_channels(
        self,
        *,
        store: MarketPort.AsyncCandleStore | MarketPort.AsyncTickerStore,
        interval_type: str,
    ) -> set[str]:
        exchanges = await self._active_catalog.get_exchanges_snap()
        channels: set[str] = set()

        for exchange_code in exchanges:
            symbols = await self._active_catalog.get_symbols_snap(
                exchange_code
            )

            for exchange_symbol in symbols:
                channels.add(
                    store.channel_key(
                        interval_type=interval_type,
                        ex=exchange_code,
                        symbol=exchange_symbol,
                    )
                )

        return channels
