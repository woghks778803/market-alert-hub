from typing import Callable, Sequence
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.datetime_utils import utcnow
from app.domain import MarketDTO, MarketRule
from app.infra.db.model import ExchangeModel 
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
    def list_exchanges(self, *, limit: int, offset: int) -> Sequence[ExchangeModel]:
        with self._uow_factory() as uow:
            return uow.markets.list_exchanges(limit=limit, offset=offset)

    def list_exchange_instruments(self, *, exchange_id: int | None, limit: int, offset: int) -> list[MarketDTO.MarketInstrumentItem]:
        with self._uow_factory() as uow:
            rows = uow.markets.list_exchange_instruments(exchange_id=exchange_id, limit=limit, offset=offset)
            return rows

    def list_mapping(self, *, exchange_id: int | None) -> list[MarketDTO.MappingItem]:
        with self._uow_factory() as uow:
            return uow.markets.list_mapping(exchange_id=exchange_id)

    # 공통 매핑
    @staticmethod
    def _to_candle_read_rows(rows) -> list[MarketDTO.CandleRead]:
        # rows: PriceSnapshot*Model instances
        return [
            MarketDTO.CandleRead(
                exchange_instrument_id=row.exchange_instrument_id,
                ts_open=row.ts_open,
                open=float(row.open),
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
                volume=float(row.volume) if getattr(row, "volume", None) is not None else None,
            )
            for row in rows
        ]

    def list_candles(
        self, *, exchange_instrument_id: int,
        base: CandleBaseInterval, output: CandleOutputInterval,
        start: datetime | None, end: datetime | None,
        limit: int, asc_order: bool,
    ) -> list[MarketDTO.CandleRead]:
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
        
    # ------------------------------------ seed snapshots data ------------------------------------------------------
    
    
    def seed_snapshots(
        self,
        *,
        base: CandleBaseInterval,
    ):
        rand = MarketRule.Randomizer(seed=42)
        n = utcnow()
        times = None
        exchanges = None
        markets = None

        if base == CandleBaseInterval.MIN_1:
            n = n.replace(second=0, microsecond=0)
            times = [n - timedelta(minutes=i) for i in range(60 * 24 * 30, 0, -1)]  # 30일분

        elif base == CandleBaseInterval.HOUR_1:
            n = n.replace(minute=0, second=0, microsecond=0)
            times = [n - timedelta(hours=i) for i in range(24*365, 0, -1)] # 1년분 

        elif base == CandleBaseInterval.DAY_1:
            n = n.replace(hour=0, minute=0, second=0, microsecond=0)
            times = [n - timedelta(days=i) for i in range(365*10, 0, -1)] # 10년분  


        with self._uow_factory() as uow:
            exchanges = uow.markets.list_exchanges()

            for ex in exchanges:
                markets = uow.markets.list_exchange_instruments(exchange_id=ex.id)

                for m in markets:
                    base_price = rand.base_price()
                    rows = []
                    for t in times:
                        rows.append({
                            "exchange_instrument_id": m.id,
                            "ts_open": t,
                            **rand.ohlcv(base_price),
                        })
                    # print(rows[-1])
                    for chunk in MarketRule.batched(rows, 6000):
                        uow.markets.seed_snapshots(interval=base, chunk=chunk)

            uow.commit()

        return True
    

    def ingest_snapshot(self, *, base: CandleBaseInterval, item: MarketDTO.CandleWrite) -> dict:
        """
        내부 writer용 단일 캔들 저장. 항상 UPSERT.
        반환: {"id": int, "created": bool}
        """
        ts = MarketRule.align_utc(item.ts_open, base, ("base", "ts_open"))
        row = {
            "exchange_instrument_id": item.exchange_instrument_id,
            "ts_open": ts,
            "open":  MarketRule.dec(item.open),
            "high":  MarketRule.dec(item.high),
            "low":   MarketRule.dec(item.low),
            "close": MarketRule.dec(item.close),
            "volume": MarketRule.dec(item.volume),
        }

        with self._uow_factory() as uow:
            
            if base == CandleBaseInterval.MIN_1:
                _id, created = uow.markets.upsert_one_1m(row)
            elif base == CandleBaseInterval.HOUR_1:
                _id, created = uow.markets.upsert_one_1h(row)
            elif base == CandleBaseInterval.DAY_1:
                _id, created = uow.markets.upsert_one_1d(row)
            else:
                raise ValueError(f"Unsupported base interval: {base}")
            
            uow.commit()

        return {"id": int(_id), "created": bool(created)}

    
