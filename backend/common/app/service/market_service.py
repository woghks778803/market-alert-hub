from tracemalloc import start
from typing import Any, Callable, Sequence, Iterable
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.constants import (
    CandleInterval,
    CandleBaseInterval,
    CandleOutputInterval,
    ExchangeCode,
    MarketSort,
)
from app.core.util.datetime import utcnow, epoch_to_datetime
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import ValidationAppError, NotFoundError
from app.domain import MarketDTO, MarketRule, MarketPort
from app.domain.market.dto import SymbolInfo


class MarketService:
    def __init__(
        self,
        *,
        uow_factory: Callable[[], UnitOfWork],
        symbol_providers: dict[str, MarketPort.ExchangeSymbol],
        snapshot_publisher: MarketPort.MarketSnapshotPublish,
    ) -> None:
        self._uow_factory = uow_factory
        self._symbol_providers = symbol_providers
        self._snapshot_publisher = snapshot_publisher

    # Meta
    def get_by_exchange_instrument_id(
        self, user_id: int, exchange_instrument_id: int
    ) -> MarketDTO.Market:
        with self._uow_factory() as uow:
            result = uow.markets.get_by_filter(
                user_id=user_id, exchange_instrument_id=exchange_instrument_id
            )

            if result is None:
                raise NotFoundError(message="Not found Market", target="market")

            return result

    def list_exchange_by_filter(
        self, *, limit: int, offset: int
    ) -> Sequence[MarketDTO.Exchange]:
        with self._uow_factory() as uow:
            return uow.markets.list_exchange_by_filter(limit=limit, offset=offset)

    def list_by_filter(
        self,
        *,
        user_id: int,
        exchange_codes: list[str] | None,
        search: str | None,
        watchlist_only: bool,
        sort: MarketSort,
        limit: int,
        offset: int,
    ) -> Sequence[MarketDTO.Market]:
        with self._uow_factory() as uow:
            rows = uow.markets.list_by_filter(
                user_id=user_id,
                exchange_codes=exchange_codes,
                search=search,
                watchlist_only=watchlist_only,
                sort=sort,
                limit=limit,
                offset=offset,
            )

            return rows

    def list_exchange_instrument_by_filter(
        self,
        *,
        exchange_id: int | None,
        is_active: bool | None = None,
        limit: int,
        offset: int,
    ) -> list[MarketDTO.MarketSimple]:
        with self._uow_factory() as uow:
            rows = uow.markets.list_exchange_instrument_by_filter(
                exchange_id=exchange_id,
                deleted_is_null=True,
                is_active=is_active,
                limit=limit,
                offset=offset,
            )
            return rows

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
                rows = uow.markets.list_snapshot_1m_by_filter(
                    exchange_instrument_id=exchange_instrument_id,
                    cursor=cursor,
                    start=start,
                    end=end,
                    limit=limit,
                    asc_order=asc_order,
                )
            elif base == CandleBaseInterval.HOUR_1:
                rows = uow.markets.list_snapshot_1h_by_filter(
                    exchange_instrument_id=exchange_instrument_id,
                    cursor=cursor,
                    start=start,
                    end=end,
                    limit=limit,
                    asc_order=asc_order,
                )
            elif base == CandleBaseInterval.DAY_1:
                rows = uow.markets.list_snapshot_1d_by_filter(
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

    # ---------------------------------------------------------------------------------------------------------------

    def sync_exchange_instruments_tickers(self):
        # 심볼별 집계 데이터 조회
        with self._uow_factory() as uow:
            tickers = uow.markets.list_ticker_stats_from_snapshots(
                is_active=True, deleted_is_null=True
            )

            uow.markets.upsert_exchange_instrument_tickers(tickers)
            uow.commit()
            return len(tickers)

    def normalize_empty_snapshots_1m(
        self, no_tick_payloads: list[dict[str, Any]], bucket_start_epoch: int
    ) -> list[MarketDTO.PriceSnapshotCreate]:
        ts_open = epoch_to_datetime(bucket_start_epoch)
        now = utcnow()
        no_tick_symbols = [
            MarketDTO.MarketSimple.from_dict(m) for m in no_tick_payloads
        ]
        ids = [s.id for s in no_tick_symbols]

        with self._uow_factory() as uow:
            last_1m_map = uow.markets.get_last_1m_by_exchange_instrument_ids(ids)

        result: list[MarketDTO.PriceSnapshotCreate] = []
        for s in no_tick_symbols:
            prev = last_1m_map.get(s.id)
            if prev is None:
                # 초기 구간(이전 캔들 없음)은 스킵
                continue

            close = prev.close  # Decimal
            result.append(
                MarketDTO.PriceSnapshotCreate(
                    exchange_instrument_id=s.id,
                    ts_open=ts_open,
                    open=close,
                    high=close,
                    low=close,
                    close=close,
                    volume=Decimal("0"),
                    updated_at=now,
                )
            )

        return result

    def normalize_snapshots_1m(
        self,
        exchange_code: str,
        payload: dict[str, Any],
        symbol_ticks: list[dict[str, Any]],
        bucket_start_epoch: int,
    ) -> MarketDTO.PriceSnapshotCreate | None:
        symbol = MarketDTO.MarketSimple.from_dict(payload)
        ts_open: datetime = epoch_to_datetime(bucket_start_epoch)
        first = symbol_ticks[0]
        last = symbol_ticks[-1]

        # high/low/volume
        high_p: Decimal | None = None
        low_p: Decimal | None = None
        vol_sum = Decimal("0")
        prev_v = None

        for t in symbol_ticks:
            p = Decimal(str(t["price"]))

            high_p = p if high_p is None else max(high_p, p)
            low_p = p if low_p is None else min(low_p, p)

            curr_v = Decimal(str(t["volume"]))

            if exchange_code == ExchangeCode.BINANCE.value:
                if prev_v is not None:
                    delta = curr_v - prev_v
                    if delta < 0:
                        delta = curr_v
                    vol_sum += delta
            elif exchange_code == ExchangeCode.UPBIT.value:
                vol_sum += curr_v
            else:
                return None

            prev_v = curr_v

        # open/close
        open_d = Decimal(str(first["price"]))
        close_d = Decimal(str(last["price"]))
        high_d = high_p if high_p is not None else open_d
        low_d = low_p if low_p is not None else open_d

        snapshot = MarketDTO.PriceSnapshotCreate(
            exchange_instrument_id=symbol.id,
            ts_open=ts_open,
            open=open_d,
            high=high_d,
            low=low_d,
            close=close_d,
            volume=vol_sum,
            updated_at=utcnow(),
        )
        return snapshot

    def sync_exchange_instruments(self, code: str):
        raw_symbols = self._symbol_providers[
            code
        ].list_symbols()  # list[MarketDTO.SymbolInfo]

        normalized = self.normalize_upbit_symbols(raw_symbols)
        with self._uow_factory() as uow:
            active = self.ensure_exchange_instruments(
                uow=uow,
                code=code,
                symbols=normalized,
            )
            uow.commit()
            return active

    def normalize_upbit_symbols(self, rows: list[SymbolInfo]) -> list:
        """
        입력/출력: MarketDTO.SymbolInfo 그대로.
        - 여기선 필터링/기본 정리만(예: KRW 마켓만, 중복 제거 등)
        """
        result = []
        seen = set()

        for r in rows:
            if r.symbol in seen:
                continue

            # parsed = MarketDTO.ParsedMarketSymbol(base=r.base, quote=r.quote)

            # 예: KRW 마켓만 사용
            # if parsed.quote != "KRW":
            #     continue

            seen.add(r.symbol)
            result.append(r)
        return result

    def ensure_exchange_instruments(
        self, *, uow: UnitOfWork, code: str, symbols: list[MarketDTO.SymbolInfo]
    ):
        """
        DB 반영(멱등 보장):
        - symbols는 MarketDTO.SymbolInfo 리스트
        """
        repo = uow.markets
        exchange = repo.get_exchange_by_filter(code=code)
        if not exchange:
            raise NotFoundError("Not found exchange", target="exchange")

        # instruments에서 활성 종목 조회
        #    (quote/base 모두 여기서 resolve)
        active_instruments = repo.list_instrument_by_filter(is_active=True)
        instrument_id_by_symbol = {i.symbol: i.id for i in active_instruments}

        # 집합 생성
        desired = set()
        symbol_by_key = {}

        for s in symbols:
            base_id = instrument_id_by_symbol.get(s.base)
            if not base_id:
                continue

            quote_id = instrument_id_by_symbol.get(s.quote)
            if not quote_id:
                continue

            key = (base_id, quote_id)
            desired.add(key)
            symbol_by_key[key] = s.symbol

        # 기존 매핑 조회
        blocked = repo.list_exchange_instrument_by_filter(
            exchange_id=exchange.id, deleted_is_null=False
        )
        existing = repo.list_exchange_instrument_by_filter(exchange_id=exchange.id)
        blocked_keys = {(m.base_asset_id, m.quote_asset_id) for m in blocked}
        existing_keys = {(m.base_asset_id, m.quote_asset_id) for m in existing}

        # print("symbol_info")
        # print(symbol_by_key)
        # print(desired)
        # print(blocked_keys)
        # print(existing_keys)

        # diff 필터
        to_insert = desired - existing_keys - blocked_keys
        to_activate = desired & existing_keys  # - blocked_keys
        to_deactivate = existing_keys - desired
        updated_at = utcnow()

        if to_insert:
            # bulk insert용
            creates = [
                MarketDTO.ExchangeInstrumentCreate(
                    exchange_id=exchange.id,
                    exchange_symbol=symbol_by_key[(base_id, quote_id)],
                    base_asset_id=base_id,
                    quote_asset_id=quote_id,
                    updated_at=updated_at,
                    is_active=True,
                )
                for (base_id, quote_id) in to_insert
            ]
            repo.add_exchange_instruments(creates)

        # 활성화
        if to_activate:
            to_activate_pairs = [
                (base_id, quote_id) for base_id, quote_id in to_activate
            ]
            repo.upsert_exchange_instruments_by_pairs(
                exchange_id=exchange.id,
                pairs=to_activate_pairs,
                is_active=True,
                updated_at=updated_at,
            )

        # 비활성화
        if to_deactivate:
            to_deactivate_pairs = [
                (base_id, quote_id) for base_id, quote_id in to_deactivate
            ]
            repo.upsert_exchange_instruments_by_pairs(
                exchange_id=exchange.id,
                pairs=to_deactivate_pairs,
                is_active=False,
                updated_at=updated_at,
            )

        uow.flush()
        # 활성 목록 반환
        return repo.list_exchange_instrument_by_filter(
            exchange_id=exchange.id, is_active=True
        )

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
            exchanges = uow.markets.list_exchange_by_filter()

            for ex in exchanges:
                markets = uow.markets.list_exchange_instrument_by_filter(
                    exchange_id=ex.id
                )

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

    def ensure_snapshot(
        self, *, base: CandleBaseInterval, item: MarketDTO.CandleBase
    ) -> dict:
        """
        내부 writer용 단일 캔들 저장. 항상 UPSERT.
        반환: {"id": int, "created": bool}
        """
        ts = MarketRule.align_utc(item.ts_open, base, ("base", "ts_open"))

        row = MarketDTO.PriceSnapshotCreate(
            exchange_instrument_id=item.exchange_instrument_id,
            ts_open=ts,
            open=MarketRule.dec(item.open),
            high=MarketRule.dec(item.high),
            low=MarketRule.dec(item.low),
            close=MarketRule.dec(item.close),
            volume=MarketRule.dec(item.volume),
            updated_at=utcnow(),
        )

        with self._uow_factory() as uow:
            # exchange_instrument_id 유효성 검사
            exchange_instrument = uow.markets.get_exchange_instrument_by_filter(
                exchange_instrument_id=item.exchange_instrument_id
            )
            if exchange_instrument is None:
                raise NotFoundError(
                    "Not found exchange instrument", target="exchange_instrument_id"
                )

            if base == CandleBaseInterval.MIN_1:
                _id, created = uow.markets.upsert_snapshot_1m(row)
            elif base == CandleBaseInterval.HOUR_1:
                _id, created = uow.markets.upsert_snapshot_1h(row)
            elif base == CandleBaseInterval.DAY_1:
                _id, created = uow.markets.upsert_snapshot_1d(row)
            else:
                raise ValidationAppError(
                    f"Unsupported base interval: {base}", target="base"
                )

            uow.commit()

        return {"id": int(_id), "created": bool(created)}

    def ensure_snapshots_1m(
        self, snapshots: list[MarketDTO.PriceSnapshotCreate]
    ) -> int:
        if not snapshots:
            return 0

        with self._uow_factory() as uow:
            ids = {s.exchange_instrument_id for s in snapshots}
            market_simples = uow.markets.list_exchange_instrument_by_filter(
                exchange_instrument_ids=ids
            )

            uow.markets.upsert_snapshots_1m(snapshots)
            uow.commit()

        self._snapshot_publisher.publish(
            MarketRule.compose_snapshot_publish_data(
                market_simples=market_simples, snapshots=snapshots
            ),
            type=CandleInterval.MIN_1.value,
        )
        return len(snapshots)

    def ensure_snapshots_1h(
        self,
        bucket_start_epoch: int,
        bucket_end_epoch: int,
    ) -> int:
        start_dt = epoch_to_datetime(bucket_start_epoch)
        end_dt = epoch_to_datetime(bucket_end_epoch)

        with self._uow_factory() as uow:
            snapshots = uow.markets.list_snapshot_1h_agg(
                start_dt=start_dt, end_dt=end_dt
            )

            ids = {s.exchange_instrument_id for s in snapshots}
            market_simples = uow.markets.list_exchange_instrument_by_filter(
                exchange_instrument_ids=ids
            )

            uow.markets.upsert_snapshots_1h(snapshots)
            uow.commit()

        self._snapshot_publisher.publish(
            MarketRule.compose_snapshot_publish_data(
                market_simples=market_simples, snapshots=snapshots
            ),
            type=CandleInterval.HOUR_1.value,
        )
        return len(snapshots)

    def ensure_snapshots_1d(
        self,
        bucket_start_epoch: int,
        bucket_end_epoch: int,
    ) -> int:
        start_dt = epoch_to_datetime(bucket_start_epoch)
        end_dt = epoch_to_datetime(bucket_end_epoch)

        with self._uow_factory() as uow:
            snapshots = uow.markets.list_snapshot_1d_agg(
                start_dt=start_dt, end_dt=end_dt
            )

            ids = {s.exchange_instrument_id for s in snapshots}
            market_simples = uow.markets.list_exchange_instrument_by_filter(
                exchange_instrument_ids=ids
            )

            uow.markets.upsert_snapshots_1d(snapshots)
            uow.commit()

        self._snapshot_publisher.publish(
            MarketRule.compose_snapshot_publish_data(
                market_simples=market_simples, snapshots=snapshots
            ),
            type=CandleInterval.DAY_1.value,
        )
        return len(snapshots)
