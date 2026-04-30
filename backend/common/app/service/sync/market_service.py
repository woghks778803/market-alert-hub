from tracemalloc import start
from typing import Any, Callable, Sequence, Iterable
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.constants import (
    TickerInterval,
    CandleInterval,
    CandleBaseInterval,
    CandleOutputInterval,
    ExchangeCode,
    MarketSort,
    BaseQuote,
)
from app.core.util.datetime import utcnow, epoch_to_datetime
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import ValidationAppError, NotFoundError
from app.domain import MarketDTO, MarketRule, MarketPort


class MarketService:
    def __init__(
        self,
        *,
        uow_factory: Callable[[], UnitOfWork],
        exchange_symbol_providers: dict[str, MarketPort.ExchangeSymbol],
        candle_store: MarketPort.CandleStore,
        market_snapshot: MarketPort.MarketSnapshot,
    ) -> None:
        self._uow_factory = uow_factory
        self._exchange_symbol_providers = exchange_symbol_providers
        self._candle_store = candle_store
        self._market_snapshot = market_snapshot

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

    def get_by_exchange_symbol(
        self, user_id: int, exchange_code: str, exchange_symbol: str
    ) -> MarketDTO.Market:
        with self._uow_factory() as uow:
            result = uow.markets.get_by_filter(
                user_id=user_id,
                exchange_code=exchange_code,
                exchange_symbol=exchange_symbol,
            )

            if result is None:
                raise NotFoundError(message="Not found Market", target="market")

            return result

    def list_exchange_by_filter(
        self, 
        *, 
        limit: int = 100,
        offset: int = 0,
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
                is_active=True,
                limit=limit,
                offset=offset,
            )

            return rows

    def list_exchange_instrument_by_filter(
        self,
        *,
        exchange_id: int | None,
        search: str | None = None,
        is_active: bool | None = None,
        limit: int,
        offset: int,
    ) -> list[MarketDTO.MarketSimple]:
        with self._uow_factory() as uow:
            rows = uow.markets.list_exchange_instrument_by_filter(
                search=search,
                exchange_id=exchange_id,
                deleted_is_null=True,
                is_active=is_active,
                limit=limit,
                offset=offset,
            )
            return rows

    def list_candle_by_filter(
        self,
        *,
        exchange_instrument_id: int,
        output: CandleOutputInterval,
        cursor: datetime | None,
        start: datetime | None,
        end: datetime | None,
        limit: int | None,
        asc_order: bool,
    ) -> list[MarketDTO.MarketCandle]:
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
            snapshots = uow.markets.list_ticker_stats_from_snapshots(
                is_active=True, deleted_is_null=True
            )

            ids = {s.exchange_instrument_id for s in snapshots}
            market_simples = uow.markets.list_exchange_instrument_by_filter(
                exchange_instrument_ids=ids
            )

            # 🔥 market lookup map
            market_map = {m.exchange_instrument_id: m for m in market_simples}

            # 🔥 BTC 기준값 찾기
            btc_krw_symbol = None
            btc_usdt_symbol = None
            eth_btc_symbol = None

            for m in market_simples:
                if (
                    m.base_symbol == BaseQuote.BTC.value
                    and m.quote_symbol == BaseQuote.KRW.value
                    and m.exchange_code == ExchangeCode.UPBIT.value
                    and m.exchange_symbol
                ):
                    btc_krw_symbol = (m.exchange_code, m.exchange_symbol)

                elif (
                    m.base_symbol == BaseQuote.BTC.value
                    and m.quote_symbol == BaseQuote.USDT.value
                    and m.exchange_code == ExchangeCode.BINANCE.value
                    and m.exchange_symbol
                ):
                    btc_usdt_symbol = (m.exchange_code, m.exchange_symbol)

                elif (
                    m.base_symbol == BaseQuote.ETH.value
                    and m.quote_symbol == BaseQuote.BTC.value
                    and m.exchange_code == ExchangeCode.BINANCE.value
                    and m.exchange_symbol
                ):
                    eth_btc_symbol = (m.exchange_code, m.exchange_symbol)

            btc_krw = None
            btc_usdt = None
            eth_btc = None

            if btc_krw_symbol:
                exchange, symbol = btc_krw_symbol
                data = self._candle_store.get_1s(exchange, symbol)
                btc_krw = Decimal(data["close"]) if data else None

            if btc_usdt_symbol:
                exchange, symbol = btc_usdt_symbol
                data = self._candle_store.get_1s(exchange, symbol)
                btc_usdt = Decimal(data["close"]) if data else None

            if eth_btc_symbol:
                exchange, symbol = eth_btc_symbol
                data = self._candle_store.get_1s(exchange, symbol)
                eth_btc = Decimal(data["close"]) if data else None

            # 🔥 normalized 계산
            for s in snapshots:
                m = market_map.get(s.exchange_instrument_id)
                if not m:
                    continue

                price = s.close_price
                volume = s.volume_24h

                normalized_price = None
                normalized_volume = None

                if m.quote_symbol == BaseQuote.KRW.value:
                    normalized_price = price

                elif m.quote_symbol == BaseQuote.BTC.value and btc_krw:
                    normalized_price = price * btc_krw

                elif m.quote_symbol == BaseQuote.USDT.value and btc_krw and btc_usdt:
                    normalized_price = price * (btc_krw / btc_usdt)

                elif m.quote_symbol == BaseQuote.ETH.value and eth_btc and btc_krw:
                    # ETH → BTC → KRW
                    normalized_price = price * eth_btc * btc_krw

                if normalized_price is not None:
                    normalized_volume = normalized_price * volume

                # 🔥 snapshots에 주입
                s.normalized_price = normalized_price or Decimal("0")
                s.normalized_volume = normalized_volume or Decimal("0")

            uow.markets.upsert_exchange_instrument_tickers(snapshots)
            uow.commit()

        self._market_snapshot.ticker_publish(
            MarketRule.compose_ticker_snapshot_data(
                market_simples=market_simples,
                snapshots=snapshots,
            ),
            interval_type=TickerInterval.HOUR_24.value,
        )

        return len(snapshots)

    def normalize_empty_snapshots_1m(
        self, no_tick_payloads: list[dict[str, Any]], bucket_start_epoch: int
    ) -> list[MarketDTO.PriceSnapshotCreate]:
        ts_open = epoch_to_datetime(bucket_start_epoch)
        now = utcnow()
        no_tick_symbols = [
            MarketDTO.MarketSimple.from_dict(m) for m in no_tick_payloads
        ]
        ids = [s.exchange_instrument_id for s in no_tick_symbols]

        with self._uow_factory() as uow:
            last_1m_map = uow.markets.get_last_1m_by_exchange_instrument_ids(ids)

        result: list[MarketDTO.PriceSnapshotCreate] = []
        for s in no_tick_symbols:
            prev = last_1m_map.get(s.exchange_instrument_id)
            if prev is None:
                # 초기 구간(이전 캔들 없음)은 스킵
                continue

            close = prev.close  # Decimal
            result.append(
                MarketDTO.PriceSnapshotCreate(
                    exchange_instrument_id=s.exchange_instrument_id,
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
            exchange_instrument_id=symbol.exchange_instrument_id,
            ts_open=ts_open,
            open=open_d,
            high=high_d,
            low=low_d,
            close=close_d,
            volume=vol_sum,
            updated_at=utcnow(),
        )
        return snapshot

    def sync_exchange_instruments(self, exchange_code: str):
        raw_symbols = self._exchange_symbol_providers[
            exchange_code
        ].list_symbols()  # list[MarketDTO.SymbolInfo]

        normalized = self.normalize_symbols(raw_symbols)
        with self._uow_factory() as uow:
            active = self.ensure_exchange_instruments(
                uow=uow,
                exchange_code=exchange_code,
                symbols=normalized,
            )
            uow.commit()
            return active

    def normalize_symbols(self, rows: list[MarketDTO.SymbolInfo]) -> list:
        """
        심볼 중복 방어용
        """
        result = []
        seen = set()

        for r in rows:
            if r.symbol in seen:
                continue

            seen.add(r.symbol)
            result.append(r)
        return result

    def ensure_exchange_instruments(
        self, *, uow: UnitOfWork, exchange_code: str, symbols: list[MarketDTO.SymbolInfo]
    ):
        """
        DB 반영(멱등 보장):
        - symbols는 MarketDTO.SymbolInfo 리스트
        """
        repo = uow.markets
        exchange = repo.get_exchange_by_filter(code=exchange_code)
        if not exchange:
            raise NotFoundError("Not found exchange", target="exchange")

        # instruments에서 활성 종목 조회
        #    (quote/base 모두 여기서 resolve)
        active_instruments = repo.list_instrument_by_filter(is_active=True)
        instrument_id_by_symbol = {i.symbol: i.id for i in active_instruments}

        # 집합 생성
        desired = set()
        symbol_info_by_key: dict[tuple[int, int], MarketDTO.SymbolInfo] = {}

        for sym in symbols:
            base_id = instrument_id_by_symbol.get(sym.base)
            if not base_id:
                continue

            quote_id = instrument_id_by_symbol.get(sym.quote)
            if not quote_id:
                continue

            key = (base_id, quote_id)
            desired.add(key)
            symbol_info_by_key[key] = sym

        # 기존 매핑 조회
        all_mappings = repo.list_exchange_instrument_by_filter(
            exchange_id=exchange.id, deleted_is_null=False
        )
        existing = repo.list_exchange_instrument_by_filter(exchange_id=exchange.id)
        all_keys  = {(m.base_asset_id, m.quote_asset_id) for m in all_mappings}
        existing_keys = {(m.base_asset_id, m.quote_asset_id) for m in existing}

        # print("symbol_info")
        # print(symbol_info_by_key)
        # print(desired)
        # print(all_keys)
        # print(existing_keys)

        # diff 필터
        to_insert = desired - all_keys
        to_activate = desired & existing_keys 
        to_deactivate = existing_keys - desired
        updated_at = utcnow()

        to_upsert = to_insert | to_activate
        if to_upsert:
            sync_items = [
                MarketDTO.ExchangeInstrumentSync(
                    exchange_id=exchange.id,
                    exchange_symbol=symbol_info_by_key[(base_id, quote_id)].symbol,
                    base_asset_id=base_id,
                    quote_asset_id=quote_id,

                    tick_size=symbol_info_by_key[(base_id, quote_id)].tick_size,
                    price_precision=symbol_info_by_key[(base_id, quote_id)].price_precision,
                    qty_precision=symbol_info_by_key[(base_id, quote_id)].qty_precision,
                    min_notional=symbol_info_by_key[(base_id, quote_id)].min_notional,

                    updated_at=updated_at,
                    is_active=True,
                )
                for base_id, quote_id in to_upsert
            ]

            repo.upsert_exchange_instruments(sync_items)

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
                                "exchange_instrument_id": m.exchange_instrument_id,
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
        self, *, base: CandleBaseInterval, item: MarketDTO.MarketCandle
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

        self._market_snapshot.candle_publish(
            MarketRule.compose_candle_snapshot_data(
                market_simples=market_simples, snapshots=snapshots
            ),
            interval_type=CandleInterval.MIN_1.value,
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

        self._market_snapshot.candle_publish(
            MarketRule.compose_candle_snapshot_data(
                market_simples=market_simples, snapshots=snapshots
            ),
            interval_type=CandleInterval.HOUR_1.value,
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

        self._market_snapshot.candle_publish(
            MarketRule.compose_candle_snapshot_data(
                market_simples=market_simples, snapshots=snapshots
            ),
            interval_type=CandleInterval.DAY_1.value,
        )
        return len(snapshots)
