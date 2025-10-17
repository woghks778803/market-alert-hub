from typing import Callable, Sequence
from datetime import datetime, timedelta

from app.core.datetime_utils import utcnow
from app.domain import MarketDTO, MarketRule, ValidationAppError, NotFoundError
from app.infra.db.model import ExchangeModel, ExchangeInstrumentModel
from app.domain.uow import UnitOfWork
from app.core.constants import CandleBaseInterval, CandleOutputInterval


class MarketService:
    def __init__(
        self,
        *,
        uow_factory: Callable[[], UnitOfWork],
    ) -> None:
        self._uow_factory = uow_factory

    # Meta
    def list_exchanges_by_filter(self, *, limit: int, offset: int) -> Sequence[ExchangeModel]:
        with self._uow_factory() as uow:
            return uow.markets.list_exchanges_by_filter(limit=limit, offset=offset)

    def list_exchange_instruments_by_filter(
        self, *, exchange_id: int | None, limit: int, offset: int
    ) -> list[MarketDTO.MarketInstrumentItem]:
        with self._uow_factory() as uow:
            rows = uow.markets.list_exchange_instruments_by_filter(
                exchange_id=exchange_id, limit=limit, offset=offset
            )
            return rows

    def list_mappings_exchange_id(self, *, exchange_id: int | None) -> list[ExchangeInstrumentModel]:
        with self._uow_factory() as uow:
            return uow.markets.list_mappings_exchange_id(exchange_id=exchange_id)

    def list_candles_by_filter(
        self,
        *,
        exchange_instrument_id: int,
        output: CandleOutputInterval,
        cursor: datetime | None,
        start: datetime | None,
        end: datetime | None,
        limit: int | None,
        asc_order: bool,
    ) -> list[MarketDTO.CandleBase]:
        # cursor 검색 우선
        if cursor is not None:
            start, end = None, None

        base = MarketRule.choose_source_base(output)
        limit = MarketRule.calc_source_limit(base, output, limit)

        with self._uow_factory() as uow:

            if base == CandleBaseInterval.MIN_1:
                rows = uow.markets.list_1m_by_filter(
                    exchange_instrument_id=exchange_instrument_id,
                    cursor=cursor,
                    start=start,
                    end=end,
                    limit=limit,
                    asc_order=asc_order,
                )
            elif base == CandleBaseInterval.HOUR_1:
                rows = uow.markets.list_1h_by_filter(
                    exchange_instrument_id=exchange_instrument_id,
                    cursor=cursor,
                    start=start,
                    end=end,
                    limit=limit,
                    asc_order=asc_order,
                )
            elif base == CandleBaseInterval.DAY_1:
                rows = uow.markets.list_1d_by_filter(
                    exchange_instrument_id=exchange_instrument_id,
                    cursor=cursor,
                    start=start,
                    end=end,
                    limit=limit,
                    asc_order=asc_order,
                )
            else:
                raise ValidationAppError(f"Unsupported base: {base}", target="base")

            if not MarketRule.same_granularity(base, output):
                # rows: ORM 모델들 (Decimal). rules.aggregate가 받아 처리
                rows = MarketRule.aggregate(rows, to=output.value, asc=asc_order)

            # limit, order 값에 따라 데이터 절삭
            if limit is not None and len(rows) > limit:
                rows = rows[-limit:] if not asc_order else rows[:limit]
            return rows

    # ------------------------------------ seed snapshots data ------------------------------------------------------

    def seed_snapshots(
        self,
        *,
        base: CandleBaseInterval,
    ) -> int:
        rand = MarketRule.Randomizer(seed=42)
        n = utcnow()
        times = None
        exchanges = None
        markets = None
        result = 0

        if base == CandleBaseInterval.MIN_1:
            n = n.replace(second=0, microsecond=0)
            times = [
                n - timedelta(minutes=i) for i in range(60 * 24 * 30, 0, -1)
            ]  # 30일분

        elif base == CandleBaseInterval.HOUR_1:
            n = n.replace(minute=0, second=0, microsecond=0)
            times = [n - timedelta(hours=i) for i in range(24 * 365, 0, -1)]  # 1년분

        elif base == CandleBaseInterval.DAY_1:
            n = n.replace(hour=0, minute=0, second=0, microsecond=0)
            times = [n - timedelta(days=i) for i in range(365 * 10, 0, -1)]  # 10년분

        with self._uow_factory() as uow:
            exchanges = uow.markets.list_exchanges_by_filter()

            for ex in exchanges:
                markets = uow.markets.list_exchange_instruments_by_filter(exchange_id=ex.id)

                for m in markets:
                    base_price = rand.base_price()
                    rows = []
                    for t in times:
                        rows.append(
                            {
                                "exchange_instrument_id": m.id,
                                "ts_open": t,
                                **rand.ohlcv(base_price),
                            }
                        )

                    for chunk in MarketRule.batched(rows, 6000):
                        uow.markets.seed_snapshots(interval=base, chunk=chunk)

                    result += len(rows)

            uow.commit()

        return result

    def ingest_snapshot(
        self, *, base: CandleBaseInterval, item: MarketDTO.CandleBase
    ) -> dict:
        """
        내부 writer용 단일 캔들 저장. 항상 UPSERT.
        반환: {"id": int, "created": bool}
        """
        ts = MarketRule.align_utc(item.ts_open, base, ("base", "ts_open"))
        row = {
            "exchange_instrument_id": item.exchange_instrument_id,
            "ts_open": ts,
            "open": MarketRule.dec(item.open),
            "high": MarketRule.dec(item.high),
            "low": MarketRule.dec(item.low),
            "close": MarketRule.dec(item.close),
            "volume": MarketRule.dec(item.volume),
        }

        with self._uow_factory() as uow:
            # exchange_instrument_id 유효성 검사
            exchange_instrument = uow.markets.get_by_exchange_instrument_id(
                exchange_instrumen_id=item.exchange_instrument_id
            )
            if exchange_instrument is None:
                raise NotFoundError(
                    "Not found exchange instrument", target="exchange_instrument_id"
                )

            if base == CandleBaseInterval.MIN_1:
                _id, created = uow.markets.upsert_1m(row)
            elif base == CandleBaseInterval.HOUR_1:
                _id, created = uow.markets.upsert_1h(row)
            elif base == CandleBaseInterval.DAY_1:
                _id, created = uow.markets.upsert_1d(row)
            else:
                raise ValidationAppError(
                    f"Unsupported base interval: {base}", target="base"
                )

            uow.commit()

        return {"id": int(_id), "created": bool(created)}
