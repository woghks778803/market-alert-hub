from typing import Callable, Sequence, Iterable
from datetime import datetime, timedelta

from app.core.constants import CandleBaseInterval, CandleOutputInterval, ExchangeCode
from app.core.util.datetime import utcnow
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import ValidationAppError, NotFoundError
from app.domain import MarketDTO, MarketRule, MarketPort


class MarketService:
    def __init__(
        self,
        *,
        uow_factory: Callable[[], UnitOfWork],
        upbit_symbol: MarketPort.UpbitSymbol,
    ) -> None:
        self._uow_factory = uow_factory
        self._upbit_symbol = upbit_symbol

    # Meta
    def list_exchange_by_filter(
        self, *, limit: int, offset: int
    ) -> Sequence[MarketDTO.Exchange]:
        with self._uow_factory() as uow:
            return uow.markets.list_exchange_by_filter(
                is_active=True, is_deleted=False, limit=limit, offset=offset
            )

    def list_exchange_instrument_by_filter(
        self,
        *,
        exchange_id: int | None,
        is_active: bool | None = None,
        limit: int,
        offset: int,
    ) -> list[MarketDTO.MappingItem]:
        with self._uow_factory() as uow:
            rows = uow.markets.list_exchange_instrument_by_filter(
                exchange_id=exchange_id,
                is_deleted=False,
                is_active=is_active,
                limit=limit,
                offset=offset,
            )
            return rows

    def list_mappings_exchange_id(
        self, *, exchange_id: int | None
    ) -> list[MarketDTO.MappingItem]:
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

    # ---------------------------------------------------------------------------------------------------------------

    def sync_exchange_instruments_from_upbit(self):
        raw_symbols = self._upbit_symbol.list_symbols()  # list[MarketDTO.SymbolInfo]

        normalized = self.normalize_upbit_symbols(raw_symbols)

        with self._uow_factory() as uow:
            active = self.ensure_exchange_instruments_from_upbit(
                uow=uow,
                symbols=normalized,
            )
            uow.commit()
            return active

    def normalize_upbit_symbols(self, rows: Iterable) -> list:
        """
        입력/출력: MarketDTO.SymbolInfo 그대로.
        - 여기선 필터링/기본 정리만(예: KRW 마켓만, 중복 제거 등)
        """
        result = []
        seen = set()

        for r in rows:
            symbol = getattr(r, "symbol", None)  # "KRW-BTC"
            if not symbol or symbol in seen:
                continue

            parsed = MarketRule.parse_market_symbol(symbol)
            if parsed is None:
                continue

            # 예: KRW 마켓만 사용
            # if parsed.quote != "KRW":
            #     continue

            seen.add(symbol)
            result.append(r)
        return result

    def ensure_exchange_instruments_from_upbit(
        self, *, uow: UnitOfWork, symbols: list[MarketDTO.SymbolInfo]
    ):
        """
        DB 반영(멱등 보장):
        - symbols는 MarketDTO.SymbolInfo 리스트
        """
        repo = uow.markets
        exchange = repo.get_exchange_by_filter(code=ExchangeCode.UPBIT)
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
            parsed = MarketRule.parse_market_symbol(
                s.symbol
            )  # "KRW-BTC" -> ("KRW", "BTC") (quote, base)
            if not parsed:
                continue

            quote, base = parsed.quote, parsed.base

            base_id = instrument_id_by_symbol.get(base)
            if not base_id:
                continue

            quote_id = instrument_id_by_symbol.get(quote)
            if not quote_id:
                continue

            key = (base_id, quote_id)
            desired.add(key)
            symbol_by_key[key] = s.symbol

        # 기존 매핑 조회
        blocked = repo.list_exchange_instrument_by_filter(
            exchange_id=exchange.id, is_deleted=True
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
                    is_deleted=False,
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
                    exchange_id=ex.id, is_deleted=False
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
            exchange_instrument = uow.markets.get_by_exchange_instrument_filter(
                exchange_instrument_id=item.exchange_instrument_id
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
