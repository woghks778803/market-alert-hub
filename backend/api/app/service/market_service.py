from typing import Callable
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random

from app.api.schema import MarketSchema
from app.domain.dto import market as MarketDTO
from app.service.uow import UnitOfWork
from app.core.constants import CandleBaseInterval, CandleOutputInterval




class MarketService:
    def __init__(
        self, 
        *,
        uow_factory: Callable[[], UnitOfWork],
    ) -> None:
        self._uow_factory = uow_factory

    # Meta
    def list_exchanges(self, *, limit: int, offset: int) -> list[MarketSchema.ExchangeRead]:
        with self._uow_factory() as uow:
            
            rows = uow.markets.list_exchanges(limit=limit, offset=offset)
            return [MarketSchema.ExchangeRead.model_validate(r) for r in rows]

    def list_exchange_instruments(self, *, exchange_id: int | None, limit: int, offset: int) -> list[MarketDTO.MarketInstrumentBrief]:
        with self._uow_factory() as uow:
            rows = uow.markets.list_exchange_instruments(exchange_id=exchange_id, limit=limit, offset=offset)
            return rows

    def list_mapping(self, *, exchange_id: int | None) -> list[MarketSchema.MappingItem]:
        with self._uow_factory() as uow:
            rows = uow.markets.list_mapping(exchange_id=exchange_id)
            return [MarketSchema.MappingItem(exchange_id=ex, instrument_id=ins) for (ex, ins) in rows]

    # Prices

    # 공통 매핑
    @staticmethod
    def _to_candle_read_rows(rows) -> list[MarketSchema.CandleRead]:
        # rows: PriceSnapshot*Model instances
        return [
            MarketSchema.CandleRead(
                exchange_id=r.exchange_id,
                instrument_id=r.instrument_id,
                ts_open=r.ts_open,
                open=float(r.open_price),
                high=float(r.high_price),
                low=float(r.low_price),
                close=float(r.close_price),
                volume=float(r.volume) if getattr(r, "volume", None) is not None else None,
            )
            for r in rows
        ]

    def list_candles(
        self, *, exchange_instrument_id: int,
        base: CandleBaseInterval, output: CandleOutputInterval,
        start: datetime | None, end: datetime | None,
        limit: int, asc_order: bool,
    ) -> list[MarketSchema.CandleRead]:
        with self._uow_factory() as uow:

            if base == CandleBaseInterval.MIN_1:

                rows = uow.markets.list_candles_1m(
                    exchange_instrument_id=exchange_instrument_id,
                    start=start, end=end,
                    limit=limit, asc_order=asc_order,
                )
            elif base == CandleBaseInterval.HOUR_1:
                rows = uow.markets.list_candles_1h(
                    exchange_instrument_id=exchange_instrument_id,
                    start=start, end=end,
                    limit=limit, asc_order=asc_order,
                )
            elif base == CandleBaseInterval.DAY_1:
                rows = uow.markets.list_candles_1d(
                    exchange_instrument_id=exchange_instrument_id,
                    start=start, end=end,
                    limit=limit, asc_order=asc_order,
                )

            return self._to_candle_read_rows(rows)
        

    
    def seed_snapshot(
        self,
        *,
        base: CandleBaseInterval,
        exchange_instrument_id: int,
        ts_open: datetime,
        open: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: Decimal,
    ):
        print(base.value)
        utcnow = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        times = None
        with self._uow_factory() as uow:

            markets = uow.markets.list_mapping

        if base == CandleBaseInterval.MIN_1:
            utcnow = utcnow.replace(second=0, microsecond=0)
            times = [utcnow - timedelta(minutes=i) for i in range(60 * 24 * 10, 0, -1)]  # 10일분

        elif base == CandleBaseInterval.HOUR_1:
            utcnow = utcnow.replace(minute=0, second=0, microsecond=0)
            times = [utcnow - timedelta(hours=i) for i in range(24*30)] # 1개월분 

        elif base == CandleBaseInterval.DAY_1:
            utcnow = utcnow.replace(hour=0, minute=0, second=0, microsecond=0)
            times = [utcnow - timedelta(days=i) for i in range(365)] # 1년분  

        print(len(times))
        print(times[0])
        print(times[-1])



        return True

