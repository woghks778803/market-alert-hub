from tracemalloc import start
from typing import Any, Callable, Sequence, Iterable
from datetime import datetime, timedelta
from decimal import Decimal

from app.core import dto as CoreDTO
from app.core.constants import (
    TickerInterval,
    CandleInterval,
    CandleBaseInterval,
    CandleOutputInterval,
    ExchangeCode,
    MarketSort,
    BaseQuote,
    OutboxStatus,
    OutboxEventType,
    BackfillRequestItemStatus,
)
from app.core.util.trace import get_trace_id
from app.core.util.datetime import utcnow, epoch_to_datetime, ensure_utc
from app.core.util.serialization import to_canonical_json
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import ValidationAppError, NotFoundError, InternalServerError
from app.domain import (
    OutboxDTO, 
    MarketDTO, 
    MarketRule, 
    MarketPort, 
    CryptoPort,
    ThrottlePort,
)


class MarketService:
    def __init__(
        self,
        *,
        uow_factory: Callable[[], UnitOfWork],
        exchange_symbol_providers: dict[str, MarketPort.ExchangeSymbol],
        exchange_candle_providers: dict[str, MarketPort.ExchangeCandle],
        candle_store: MarketPort.CandleStore,
        market_snapshot: MarketPort.MarketSnapshot,
        cooldown: ThrottlePort.Cooldown,
        hmac: CryptoPort.TokenHasher,
        config: CoreDTO.ServiceConfigBag,
    ) -> None:
        self._uow_factory = uow_factory
        self._exchange_symbol_providers = exchange_symbol_providers
        self._exchange_candle_providers = exchange_candle_providers
        self._candle_store = candle_store
        self._market_snapshot = market_snapshot
        self._cooldown = cooldown
        self._hmac = hmac
        self._config = config

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
    
    def create_backfill_request(
        self,
        *,
        user_id: int,
        exchange_instrument_ids: list[int],
        base: CandleBaseInterval,
        start_at: datetime,
        end_at: datetime,
        reason: str,
    ):
        with self._uow_factory() as uow:
            # 값 검증
            exchange_instrument_ids = list(dict.fromkeys(exchange_instrument_ids))
            reason = reason.strip()
            
            if start_at >= end_at:
                raise ValidationAppError("start_at must be earlier than end_at", target="start_at")

            if not exchange_instrument_ids:
                raise ValidationAppError("exchange_instrument_ids is required", target="exchange_instrument_ids")

            if not reason:
                raise ValidationAppError(
                    "reason is required",
                    target="reason",
                )

            # exchange_instrument_ids 검색
            market_simples = uow.markets.list_exchange_instrument_by_filter(
                exchange_instrument_ids=exchange_instrument_ids,
                is_active=True,
            )

            if(len(market_simples) != len(exchange_instrument_ids)):
                raise ValidationAppError(f"Invalid exchange_instrument_ids", target="exchange_instrument_ids")

            # backfill_request 생성
            backfill_request = uow.markets.add_backfile_request(
                row=MarketDTO.BackfillRequestCreate(
                    user_id=user_id,
                    base=base,
                    start_at=start_at,
                    end_at=end_at,
                    reason=reason,
                )
            )

            # backfill_request_itme 생성
            items = [
                MarketDTO.BackfillRequestItemCreate(
                    backfill_request_id=backfill_request.id,
                    exchange_instrument_id=exchange_instrument_id,
                )
                for exchange_instrument_id in exchange_instrument_ids
            ]

            uow.markets.add_backfill_request_items(rows=items)

            # outbox 생성
            fp_dict: dict[str, Any] = {
                "event_type": OutboxEventType.REQUEST_MARKET_BACKFILL.value,
                "aggregate_type": "backfill_request",
                "aggregate_id": backfill_request.id,
            }

            outbox_fingerprint = to_canonical_json(fp_dict)
            outbox_fingerprint = (
                self._hmac.fp_hash(outbox_fingerprint)
                if outbox_fingerprint is not None
                else None
            )

            # 4) outbox enqueue
            uow.outboxs.add_outbox(
                OutboxDTO.OutboxCreate(
                    trace_id=get_trace_id(),
                    event_type=OutboxEventType.REQUEST_MARKET_BACKFILL,
                    aggregate_type="backfill_request",
                    aggregate_id=backfill_request.id,
                    outbox_fingerprint=outbox_fingerprint,
                    payload={
                        "backfill_request_id": backfill_request.id,
                    },
                    status=OutboxStatus.PENDING,
                    attempts=0,
                ),
                True,
            )

            uow.commit()

            return backfill_request

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

            # market lookup map
            market_map = {m.exchange_instrument_id: m for m in market_simples}

            # BTC 기준값 찾기
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

            # normalized 계산
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

                # snapshots에 주입
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
        ].list_symbol()  # list[MarketDTO.SymbolInfo]

        normalized = self.normalize_symbols(raw_symbols)
        with self._uow_factory() as uow:
            actives = self.ensure_exchange_instruments(
                uow=uow,
                exchange_code=exchange_code,
                symbols=normalized,
            )
            uow.commit()
            return actives

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


    def request_market_backfills(
        self,
        *,
        backfill_request_id: int,
        job_batch_size: int,
        api_batch_size: int,
    ) -> dict[str, Any]:
        # 이 경우 outbox_fingerprint는 관리자 API 중복 요청 방지용으로만 사용하고 requeue에선 None 처리
        now = utcnow()
        blocked_exchanges: set[str] = set()

        # 1) 처리할 job 조회
        with self._uow_factory() as uow:
            jobs = uow.markets.list_backfill_job_by_filter(
                backfill_request_id=backfill_request_id,
                statuses=[
                    MarketDTO.BackfillRequestItemStatus.QUEUED,
                    MarketDTO.BackfillRequestItemStatus.RETRY_WAIT,
                ],
                limit=job_batch_size + 1,
            )

        if not jobs:
            return {
                "backfill_request_id": backfill_request_id,
                "processed_items": 0,
                "completed_items": 0,
                "retry_wait_items": 0,
                "failed_items": 0,
                "reason": "no_pending_items",
            }

        should_requeue = len(jobs) > job_batch_size
        processed_items = 0
        completed_items = 0
        retry_wait_items = 0
        failed_items = 0

        # 2) 이번 worker 실행에서 처리할 item 수 제한
        for job in jobs[:job_batch_size]:
            if job.exchange_code in blocked_exchanges:
                continue

            # 3) item claim: queued/retry_wait -> running
            with self._uow_factory() as uow:
                claimed = uow.markets.update_backfill_request_item_status(
                    backfill_request_item_id=job.backfill_request_item_id,
                    from_statuses=[
                        MarketDTO.BackfillRequestItemStatus.QUEUED,
                        MarketDTO.BackfillRequestItemStatus.RETRY_WAIT,
                    ],
                    to_status=MarketDTO.BackfillRequestItemStatus.RUNNING
                )
                uow.commit()

            if not claimed:
                continue
            
            processed_items += 1

            total_fetched_count = 0
            total_upserted_count = 0
            start_at = ensure_utc(job.start_at)
            end_at = ensure_utc(job.end_at)
            current_to = ensure_utc(job.cursor_at or job.end_at)

            try:
                # 4) 거래소별 기본값
                exchange_code = job.exchange_code

                if exchange_code == ExchangeCode.UPBIT.value:
                    candle_batch_size = self._config.upbit_candle_batch_size
                    candle_rate_limit = self._config.upbit_candle_rate_limit

                    if candle_batch_size <= 0:
                        raise InternalServerError(f"invalid upbit_candle_batch_size: {candle_batch_size}", target="candle_batch_size")

                    if candle_rate_limit <= 0:
                        raise InternalServerError(f"invalid upbit_candle_rate_limit_count: {candle_rate_limit}", target="candle_rate_limit")

                    candle_provider = self._exchange_candle_providers[ExchangeCode.UPBIT.value]

                elif exchange_code == ExchangeCode.BINANCE.value:
                    candle_batch_size = self._config.binance_candle_batch_size
                    candle_rate_limit = self._config.binance_candle_rate_limit

                    if candle_batch_size <= 0:
                        raise InternalServerError(f"invalid binance_candle_batch_size: {candle_batch_size}", target="candle_batch_size")

                    if candle_rate_limit <= 0:
                        raise InternalServerError(f"invalid binance_candle_rate_limit: {candle_rate_limit}", target="candle_rate_limit")

                    candle_provider = self._exchange_candle_providers[ExchangeCode.BINANCE.value]

                else:
                    raise ValidationAppError(
                        f"unsupported exchange for backfill: {job.exchange_code}", 
                        target="job.exchange_code",
                        meta={"exchange_code" : job.exchange_code}
                    )

                completed = False
                last_cursor_at = current_to

                # 5) 이번 worker 실행에서 API batch N번까지만 처리
                for _ in range(api_batch_size):
                    # 5-1) Redis rate limit: 초당 5회 같은 제한
                    current_count = self._cooldown.incr_exchange_candle_rate_limit(
                        exchange_code=exchange_code,
                        ttl_sec=1,
                    )

                    if current_count > candle_rate_limit:
                        # 호출하지 않고 다음 outbox로 넘김
                        with self._uow_factory() as uow:
                            uow.markets.update_backfill_request_item(
                                backfill_request_item_id=job.backfill_request_item_id,
                                from_status=MarketDTO.BackfillRequestItemStatus.RUNNING,
                                to_status=MarketDTO.BackfillRequestItemStatus.RETRY_WAIT,
                                cursor_at=current_to,
                                result_code="rate_limit",
                                result_message="exchange candle rate limit exceeded",
                                result_payload={
                                    "fetched_count": total_fetched_count,
                                    "upserted_count": total_upserted_count,
                                    "cursor_at": current_to.isoformat(),
                                },
                            )

                            uow.commit()

                        retry_wait_items += 1
                        should_requeue = True
                        blocked_exchanges.add(exchange_code)
                        
                        break
                        # return {
                        #     "backfill_request_id": backfill_request_id,
                        #     "processed_items": processed_items,
                        #     "completed_items": completed_items,
                        #     "retry_wait_items": retry_wait_items,
                        #     "failed_items": failed_items,
                        #     "reason": "rate_limit",
                        # }

                    # 5-2) API 호출 1회 = api batch 1개
                    exchange_candles = candle_provider.list_candle(
                        base=job.base,
                        exchange_symbol=job.exchange_symbol,
                        to=current_to,
                        count=candle_batch_size,
                    )

                    if exchange_candles is None:
                        raise ValidationAppError(
                            "unsupported exchange candle base interval",
                            target="job.base",
                            meta={"base": job.base.value},
                        )

                    if not exchange_candles:
                        # 더 가져올 데이터 없음
                        completed = True
                        break

                    # 다음 cursor 계산
                    # candle gap이 크면 범위 안에 저장할 candle이 없을 수 있으니 cursor는 거래소에서 제공하는 exchange_candle로 계산
                    opened_times = [
                        exchange_candle.opened_at
                        for exchange_candle in exchange_candles
                    ]

                    oldest_opened_at = min(opened_times)
                    last_cursor_at = oldest_opened_at

                    total_fetched_count += len(exchange_candles)

                    interval = MarketRule.choose_candle_interval_delta(job.base)

                    window_end_at = min(current_to, end_at)

                    candles = MarketRule.fill_candle_gaps(
                        candles=exchange_candles,
                        start_at=start_at,
                        end_at=window_end_at,
                        interval=interval,
                    )

                    # 5-3) 응답 -> 내부 candle row 변환
                    snapshots = [
                        MarketDTO.PriceSnapshotCreate(
                            exchange_instrument_id=job.exchange_instrument_id,
                            ts_open=candle.opened_at,
                            open=candle.open_price,
                            high=candle.high_price,
                            low=candle.low_price,
                            close=candle.close_price,
                            volume=candle.volume,
                            updated_at=now,
                        )
                        for candle in candles
                    ]

                    # 5-4) 저장
                    if snapshots:
                        # upsert 대상으로 넘긴 candle row 수
                        saved_count = len(snapshots)

                        with self._uow_factory() as uow:
                            if job.base == CandleBaseInterval.MIN_1:
                                uow.markets.upsert_snapshots_1m(rows=snapshots)
                            elif job.base == CandleBaseInterval.HOUR_1:
                                uow.markets.upsert_snapshots_1h(rows=snapshots)
                            elif job.base == CandleBaseInterval.DAY_1:
                                uow.markets.upsert_snapshots_1d(rows=snapshots)
                            else:
                                raise ValidationAppError(
                                    "unsupported candle base interval",
                                    target="job.base",
                                    meta={"base": job.base.value},
                                )
             
                            uow.commit()

                        total_upserted_count += saved_count

                    # start_at까지 내려왔으면 완료
                    if oldest_opened_at <= start_at:
                        completed = True
                        break

                    # 아직 더 과거로 내려가야 하면 다음 API 호출의 to로 사용
                    current_to = oldest_opened_at

                # 6) 상태 마무리
                if completed:
                    with self._uow_factory() as uow:
                        uow.markets.update_backfill_request_item(
                            backfill_request_item_id=job.backfill_request_item_id,
                            from_status=MarketDTO.BackfillRequestItemStatus.RUNNING,
                            to_status=MarketDTO.BackfillRequestItemStatus.COMPLETED,
                            result_code="completed",
                            result_message=None,
                            result_payload={
                                "fetched_count": total_fetched_count,
                                "upserted_count": total_upserted_count,
                                "cursor_at": None,
                            },
                        )
                        uow.commit()

                    completed_items += 1

                else:
                    with self._uow_factory() as uow:
                        uow.markets.update_backfill_request_item(
                            backfill_request_item_id=job.backfill_request_item_id,
                            from_status=MarketDTO.BackfillRequestItemStatus.RUNNING,
                            to_status=MarketDTO.BackfillRequestItemStatus.RETRY_WAIT,
                            cursor_at=last_cursor_at,
                            result_code="yield",
                            result_message="max api batches per run reached",
                            result_payload={
                                "fetched_count": total_fetched_count,
                                "upserted_count": total_upserted_count,
                                "cursor_at": last_cursor_at.isoformat(),
                            },
                        )

                        uow.commit()

                    retry_wait_items += 1
                    should_requeue = True

                if should_requeue:
                    with self._uow_factory() as uow:
                        uow.outboxs.add_outbox(
                            OutboxDTO.OutboxCreate(
                                trace_id=get_trace_id(),
                                event_type=OutboxEventType.REQUEST_MARKET_BACKFILL,
                                aggregate_type="backfill_request",
                                aggregate_id=backfill_request_id,
                                payload={
                                    "backfill_request_id": backfill_request_id,
                                },
                                status=OutboxStatus.PENDING,
                                attempts=0,
                                next_run_at=utcnow() + timedelta(seconds=10),
                                outbox_fingerprint=None,
                            ),
                            True,
                        )
                        
                        uow.commit()

            except Exception as e:
                with self._uow_factory() as uow:
                    uow.markets.update_backfill_request_item(
                        backfill_request_item_id=job.backfill_request_item_id,
                        from_status=MarketDTO.BackfillRequestItemStatus.RUNNING,
                        to_status=MarketDTO.BackfillRequestItemStatus.FAILED,
                        result_code=e.__class__.__name__[:64],
                        result_message=str(e),
                        result_payload={
                            "fetched_count": total_fetched_count,
                            "upserted_count": total_upserted_count,
                            "cursor_at": current_to.isoformat() if current_to else None,
                        },
                    )
                    uow.commit()

                failed_items += 1

        return {
            "backfill_request_id": backfill_request_id,
            "processed_items": processed_items,
            "completed_items": completed_items,
            "retry_wait_items": retry_wait_items,
            "failed_items": failed_items,
        }


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
