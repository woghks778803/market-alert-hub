from cProfile import label
from decimal import Decimal
from typing import cast, Sequence, Tuple
from sqlalchemy.engine import CursorResult
from sqlalchemy import update, insert, select, and_, or_, asc, desc, func, tuple_
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import aliased, Session as DbSession
from app.infra.db.model import (
    ExchangeModel,
    InstrumentModel,
    ExchangeInstrumentModel,
    ExchangeInstrumentTickerModel,
    PriceSnapshot1mModel,
    PriceSnapshot1hModel,
    PriceSnapshot1dModel,
    WatchlistItemModel,
)
from app.core.util.datetime import utcnow, get_days_ago
from app.core.constants import MarketSort
from app.domain import MarketDTO
from datetime import datetime
from app.infra.db.repository.protocol.market_repo import MarketRepo
from app.infra.db.utils import to_row_dict

eit = ExchangeInstrumentTickerModel
ei = ExchangeInstrumentModel
e = ExchangeModel
base = aliased(InstrumentModel)
quote = aliased(InstrumentModel)
wi = WatchlistItemModel
ps1m = PriceSnapshot1mModel
ps1h = PriceSnapshot1hModel
ps1d = PriceSnapshot1dModel


class SqlMarketRepo(MarketRepo):
    def __init__(self, db: DbSession):
        self._db = db

    def list_ticker_stats_from_snapshots(
        self, is_active: bool, deleted_is_null: bool = True
    ) -> list[MarketDTO.ExchangeInstrumentTickerCreate]:
        ps_agg = aliased(ps1m)
        ps_open = aliased(ps1m)
        ps_close = aliased(ps1m)

        latest_1d = (
            select(
                ps_agg.exchange_instrument_id.label("ei_id"),
                func.min(ps_agg.ts_open).label("open_24h"),
                func.max(ps_agg.ts_open).label("close_24h"),
                func.max(ps_agg.high).label("high_24h"),
                func.min(ps_agg.low).label("low_24h"),
                func.sum(ps_agg.volume).label("volume_24h"),
            )
            .join(
                ei,
                ei.id == ps_agg.exchange_instrument_id,
            )
            .where(
                ps_agg.ts_open >= get_days_ago(utcnow(), 1),
            )
        )

        if is_active:
            latest_1d = latest_1d.where(ei.is_active.is_(is_active))
        if deleted_is_null:
            latest_1d = latest_1d.where(ei.deleted_at.is_(None))

        latest_1d = latest_1d.group_by(ps_agg.exchange_instrument_id).subquery()

        # select에 등장한 첫 selectable을 기준으로 FROM
        stmt = (
            select(
                latest_1d.c.ei_id,
                ps_open.open.label("open_price"),
                ps_close.close.label("close_price"),
                latest_1d.c.high_24h,
                latest_1d.c.low_24h,
                latest_1d.c.volume_24h,
                # 이건 ps_open.open null 값을 허용하진않지만 안전빵
                func.coalesce((ps_close.close - ps_open.open), 0).label(
                    "price_change_24h"
                ),
                (
                    func.coalesce(
                        (ps_close.close - ps_open.open)
                        / func.nullif(ps_open.open, 0)
                        * 100,
                        0,
                    )
                ).label("price_change_rate_24h"),
            )
            .select_from(latest_1d)
            .join(
                ps_open,
                and_(
                    ps_open.exchange_instrument_id == latest_1d.c.ei_id,
                    ps_open.ts_open == latest_1d.c.open_24h,
                ),
            )
            .join(
                ps_close,
                and_(
                    ps_close.exchange_instrument_id == latest_1d.c.ei_id,
                    ps_close.ts_open == latest_1d.c.close_24h,
                ),
            )
        )

        rows = self._db.execute(stmt).all()
        return [
            MarketDTO.ExchangeInstrumentTickerCreate(
                exchange_instrument_id=row.ei_id,
                open_price=row.open_price,
                close_price=row.close_price,
                high_24h=row.high_24h,
                low_24h=row.low_24h,
                volume_24h=row.volume_24h,
                price_change_24h=row.price_change_24h,
                price_change_rate_24h=row.price_change_rate_24h,
            )
            for row in rows
        ]

    def get_by_filter(
        self,
        user_id: int,
        exchange_instrument_id: int | None = None,
        exchange_code: str | None = None,
        exchange_symbol: str | None = None,
        is_active: bool = True,
        deleted_is_null: bool = True,
    ) -> MarketDTO.Market | None:
        if exchange_instrument_id is None and not (exchange_code and exchange_symbol):
            return None

        stmt = (
            select(
                ei.id,
                ei.exchange_symbol.label("exchange_symbol"),
                e.code.label("exchange_code"),
                e.name.label("exchange_name"),
                base.symbol.label("base_symbol"),
                quote.symbol.label("quote_symbol"),
                base.name.label("asset_name"),
                eit.open_price,
                eit.close_price,
                eit.high_24h,
                eit.low_24h,
                eit.volume_24h,
                eit.price_change_24h,
                eit.price_change_rate_24h,
                eit.normalized_price,
                eit.normalized_volume,
                wi.id.label("watchlist_id"),
            )
            .join(e, ei.exchange_id == e.id)
            .join(base, ei.base_asset_id == base.id)
            .join(quote, ei.quote_asset_id == quote.id)
            .outerjoin(eit, eit.exchange_instrument_id == ei.id)
            .outerjoin(
                wi,
                and_(
                    wi.exchange_instrument_id == ei.id,
                    wi.user_id == user_id,
                ),
            )
            .where(ei.is_active == is_active)
        )

        if exchange_instrument_id is not None:
            stmt = stmt.where(ei.id == exchange_instrument_id)
        elif exchange_code is not None and exchange_symbol is not None:
            stmt = stmt.where(
                and_(
                    e.code == exchange_code,
                    ei.exchange_symbol == exchange_symbol,
                )
            )

        if deleted_is_null:
            stmt = stmt.where(ei.deleted_at.is_(None))

        row = self._db.execute(stmt).one_or_none()

        if row is None:
            return None

        return MarketDTO.Market(
            exchange_instrument_id=row.id,
            exchange_symbol=row.exchange_symbol,
            exchange_code=row.exchange_code,
            exchange_name=row.exchange_name,
            base_symbol=row.base_symbol,  
            quote_symbol=row.quote_symbol,
            asset_name=row.asset_name,
            high_24h=row.high_24h if row.high_24h is not None else None,
            low_24h=row.low_24h if row.low_24h is not None else None,
            volume_24h=row.volume_24h if row.volume_24h is not None else None,
            open_price=row.open_price if row.open_price is not None else None,
            close_price=row.close_price if row.close_price is not None else None,
            price_change_24h=(
                row.price_change_24h if row.price_change_24h is not None else None
            ),
            price_change_rate_24h=(
                row.price_change_rate_24h
                if row.price_change_rate_24h is not None
                else None
            ),
            normalized_price=(
                row.normalized_price if row.normalized_price is not None else None
            ),
            normalized_volume=(
                row.normalized_volume if row.normalized_volume is not None else None
            ),
            is_watchlisted=row.watchlist_id is not None,
        )

    def get_exchange_by_filter(
        self,
        id: int | None = None,
        code: str | None = None,
        is_active: bool = True,
        deleted_is_null: bool = True,
    ) -> MarketDTO.Exchange | None:
        stmt = select(e).where(e.is_active.is_(is_active))
        if deleted_is_null:
            stmt = stmt.where(e.deleted_at.is_(None))
        if id is not None:
            stmt = stmt.where(e.id == id)
        if code is not None:
            stmt = stmt.where(e.code == code)

        exchange = self._db.execute(stmt).scalars().one_or_none()
        if exchange is None:
            return None
        return exchange.to_dto()

    def get_exchange_instrument_by_filter(
        self,
        *,
        exchange_instrument_id: int,
        is_active: bool = True,
        deleted_is_null: bool = True,
    ) -> MarketDTO.ExchangeInstrument | None:
        stmt = select(ei).where(
            and_(
                ei.is_active.is_(is_active),
                ei.id == exchange_instrument_id,
            )
        )
        if deleted_is_null:
            stmt = stmt.where(ei.deleted_at.is_(None))

        exchange_instrument = self._db.execute(stmt).scalars().one_or_none()
        if exchange_instrument is None:
            return None
        return exchange_instrument.to_dto()

    def get_last_1m_by_exchange_instrument_ids(
        self,
        exchange_instrument_ids: list[int],
    ) -> dict[int, MarketDTO.PriceSnapshot]:
        """
        exchange_instrument_id별로 가장 최신(최대 ts_open) 1분봉을 bulk로 조회해서 dict로 반환.
        """
        ids = [int(x) for x in exchange_instrument_ids]
        if not ids:
            return {}

        subq = (
            select(
                ps1m.exchange_instrument_id,
                func.max(ps1m.ts_open).label("max_ts_open"),
            )
            .where(ps1m.exchange_instrument_id.in_(ids))
            .group_by(ps1m.exchange_instrument_id)
            .subquery()
        )

        stmt = select(ps1m).join(
            subq,
            and_(
                ps1m.exchange_instrument_id == subq.c.exchange_instrument_id,
                ps1m.ts_open == subq.c.max_ts_open,
            ),
        )

        rows = self._db.execute(stmt).scalars().all()

        out: dict[int, MarketDTO.PriceSnapshot] = {}
        for m in rows:
            dto = m.to_dto()  # type: ignore[attr-defined]
            out[dto.exchange_instrument_id] = dto

        return out

    # Meta
    def list_exchange_by_filter(
        self,
        *,
        is_active: bool = True,
        deleted_is_null: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[MarketDTO.Exchange]:
        stmt = (
            select(ExchangeModel)
            .where(
                and_(
                    ExchangeModel.is_active.is_(is_active),
                )
            )
            .order_by(asc(ExchangeModel.id))
            .limit(limit)
            .offset(offset)
        )
        if deleted_is_null:
            stmt = stmt.where(ExchangeModel.deleted_at.is_(None))

        rows = self._db.execute(stmt).scalars().all()
        return [row.to_dto() for row in rows]

    def list_by_filter(
        self,
        *,
        user_id: int,
        exchange_codes: list[str] | None,
        search: str | None,
        watchlist_only: bool,
        sort: MarketSort,
        is_active: bool | None = None,
        limit: int,
        offset: int,
    ) -> Sequence[MarketDTO.Market]:
        stmt = (
            select(
                ei.id,
                ei.exchange_symbol.label("exchange_symbol"),
                e.code.label("exchange_code"),
                e.name.label("exchange_name"),
                base.symbol.label("base_symbol"),
                quote.symbol.label("quote_symbol"),
                base.name.label("asset_name"),
                wi.id.label("watchlist_id"),
                eit.open_price,
                eit.close_price,
                eit.high_24h,
                eit.low_24h,
                eit.volume_24h,
                eit.price_change_24h,
                eit.price_change_rate_24h,
                eit.normalized_price,
                eit.normalized_volume,
            )
            .join(e, ei.exchange_id == e.id)
            .join(base, ei.base_asset_id == base.id)
            .join(quote, ei.quote_asset_id == quote.id)
        )

        stmt = stmt.outerjoin(eit, eit.exchange_instrument_id == ei.id)

        conditions = []

        if is_active is not None:
            conditions.append(ei.is_active.is_(is_active))

        # 거래소 필터
        if exchange_codes:
            conditions.append(e.code.in_(exchange_codes))

        # 검색
        if search:
            conditions.append(
                or_(
                    base.symbol.ilike(f"%{search}%"),
                    base.name.ilike(f"%{search}%"),
                    quote.symbol.ilike(f"%{search}%"),
                    quote.name.ilike(f"%{search}%"),
                    ei.exchange_symbol.ilike(f"%{search}%"),
                    e.code.ilike(f"%{search}%"),
                    e.name.ilike(f"%{search}%"),
                )
            )

        # 즐겨찾기 join
        if watchlist_only:
            stmt = stmt.join(
                wi,
                and_(
                    wi.exchange_instrument_id == ei.id,
                    wi.user_id == user_id,
                ),
            )
        else:
            stmt = stmt.outerjoin(
                wi,
                and_(
                    wi.exchange_instrument_id == ei.id,
                    wi.user_id == user_id,
                ),
            )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # 정렬
        if sort == MarketSort.VOLUME_DESC:
            stmt = stmt.order_by(desc(eit.normalized_volume))

        elif sort == MarketSort.CHANGE_DESC:
            stmt = stmt.order_by(desc(eit.price_change_rate_24h))

        elif sort == MarketSort.CHANGE_ASC:
            stmt = stmt.order_by(asc(eit.price_change_rate_24h))

        elif sort == MarketSort.PRICE_DESC:
            stmt = stmt.order_by(desc(eit.normalized_price))

        elif sort == MarketSort.PRICE_ASC:
            stmt = stmt.order_by(asc(eit.normalized_price))

        else:
            stmt = stmt.order_by(desc(eit.normalized_volume))

        stmt = stmt.limit(limit).offset(offset)
        rows = self._db.execute(stmt).all()

        return [
            MarketDTO.Market(
                exchange_instrument_id=row.id,
                exchange_symbol=row.exchange_symbol,
                exchange_code=row.exchange_code,
                exchange_name=row.exchange_name,
                base_symbol=row.base_symbol,  
                quote_symbol=row.quote_symbol,
                asset_name=row.asset_name,
                high_24h=row.high_24h if row.high_24h is not None else None,
                low_24h=row.low_24h if row.low_24h is not None else None,
                volume_24h=row.volume_24h if row.volume_24h is not None else None,
                open_price=row.open_price if row.open_price is not None else None,
                close_price=row.close_price if row.close_price is not None else None,
                price_change_24h=(
                    row.price_change_24h if row.price_change_24h is not None else None
                ),
                price_change_rate_24h=(
                    row.price_change_rate_24h
                    if row.price_change_rate_24h is not None
                    else None
                ),
                normalized_price=(
                    row.normalized_price if row.normalized_price is not None else None
                ),
                normalized_volume=(
                    row.normalized_volume if row.normalized_volume is not None else None
                ),
                is_watchlisted=row.watchlist_id is not None,
            )
            for row in rows
        ]

    def list_instrument_by_filter(
        self,
        *,
        is_active: bool | None = None,
        deleted_is_null: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[MarketDTO.Instrument]:
        stmt = (
            select(InstrumentModel)
            .order_by(asc(InstrumentModel.id))
            .limit(limit)
            .offset(offset)
        )

        if deleted_is_null:
            stmt = stmt.where(InstrumentModel.deleted_at.is_(None))

        if is_active is not None:
            stmt = stmt.where(InstrumentModel.is_active.is_(is_active))

        rows = self._db.execute(stmt).scalars().all()

        return [row.to_dto() for row in rows]

    def list_exchange_instrument_by_filter(
        self,
        *,
        search: str | None = None,
        exchange_instrument_ids: set[int] | None = None,
        exchange_id: int | None = None,
        is_active: bool | None = None,
        deleted_is_null: bool = True,
        limit: int = 200,
        offset: int = 0,
    ) -> list[MarketDTO.MarketSimple]:

        stmt = (
            select(
                ei.id.label("exchange_instrument_id"),
                ei.exchange_symbol.label("exchange_symbol"),
                ei.base_asset_id,
                ei.quote_asset_id,
                base.symbol.label("base_symbol"),
                quote.symbol.label("quote_symbol"),
                e.id.label("exchange_id"),
                e.name.label("exchange_name"),
                e.code.label("exchange_code"),
            )
            .select_from(ei)
            .join(e, ei.exchange)
            .join(base, ei.base_asset)
            .join(quote, ei.quote_asset)
            .order_by(asc(ei.exchange_symbol))
            .limit(limit)
            .offset(offset)
        )

        conditions = []
        
        if search:
            conditions.append(
                or_(
                    base.symbol.ilike(f"%{search}%"),
                    quote.symbol.ilike(f"%{search}%"),
                    e.name.ilike(f"%{search}%"),
                    ei.exchange_symbol.ilike(f"%{search}%"),
                )
            )

        if deleted_is_null:
            stmt = stmt.where(
                and_(
                    ei.deleted_at.is_(None),
                    base.deleted_at.is_(None),
                    quote.deleted_at.is_(None),
                )
            )
        if is_active is not None:
            stmt = stmt.where(ei.is_active == is_active)
        if exchange_id is not None:
            stmt = stmt.where(ei.exchange_id == exchange_id)
        if exchange_instrument_ids is not None:
            stmt = stmt.where(ei.id.in_(exchange_instrument_ids))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        rows = self._db.execute(stmt).mappings().all()

        return [MarketDTO.MarketSimple(**row) for row in rows]

    # 공통 빌더
    def _list_snapshot_by_filter(
        self,
        model,
        *,
        exchange_instrument_id: int,
        cursor: datetime | None,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        asc_order: bool,
    ) -> list[MarketDTO.MarketCandle]:
        wheres = [
            model.exchange_instrument_id == exchange_instrument_id,
        ]
        if cursor is not None:
            wheres.append(model.ts_open < cursor)
        else:
            if start is not None:
                wheres.append(model.ts_open >= start)
            if end is not None:
                wheres.append(model.ts_open < end)

        order_by = asc(model.ts_open) if asc_order else desc(model.ts_open)

        stmt = select(model).where(and_(*wheres)).order_by(order_by).limit(limit)

        rows = self._db.execute(stmt).scalars().all()

        return [
            MarketDTO.MarketCandle(
                exchange_instrument_id=row.exchange_instrument_id,
                ts_open=row.ts_open,
                open=float(row.open),
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
                volume=float(row.volume),
            )
            for row in rows
        ]

    # 1m/1h/1d 개별 메서드
    def list_snapshot_1m_by_filter(
        self,
        *,
        exchange_instrument_id: int,
        cursor: datetime | None,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        asc_order: bool,
    ) -> list[MarketDTO.MarketCandle]:
        return self._list_snapshot_by_filter(
            PriceSnapshot1mModel,
            exchange_instrument_id=exchange_instrument_id,
            cursor=cursor,
            start=start,
            end=end,
            limit=limit,
            asc_order=asc_order,
        )

    def list_snapshot_1h_by_filter(
        self,
        *,
        exchange_instrument_id: int,
        cursor: datetime | None,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        asc_order: bool,
    ) -> list[MarketDTO.MarketCandle]:
        return self._list_snapshot_by_filter(
            PriceSnapshot1hModel,
            exchange_instrument_id=exchange_instrument_id,
            cursor=cursor,
            start=start,
            end=end,
            limit=limit,
            asc_order=asc_order,
        )

    def list_snapshot_1d_by_filter(
        self,
        *,
        exchange_instrument_id: int,
        cursor: datetime | None,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        asc_order: bool,
    ) -> list[MarketDTO.MarketCandle]:
        return self._list_snapshot_by_filter(
            PriceSnapshot1dModel,
            exchange_instrument_id=exchange_instrument_id,
            cursor=cursor,
            start=start,
            end=end,
            limit=limit,
            asc_order=asc_order,
        )

    def list_snapshot_1h_agg(
        self,
        *,
        start_dt: datetime,
        end_dt: datetime,
    ) -> list[MarketDTO.PriceSnapshotCreate]:
        agg_sq = (
            select(
                ps1m.exchange_instrument_id.label("exchange_instrument_id"),
                func.max(ps1m.high).label("high"),
                func.min(ps1m.low).label("low"),
                func.sum(ps1m.volume).label("volume"),
                func.min(ps1m.ts_open).label("ts_open_min"),
                func.max(ps1m.ts_open).label("ts_open_max"),
            )
            .where(ps1m.ts_open >= start_dt, ps1m.ts_open < end_dt)
            .group_by(ps1m.exchange_instrument_id)
            .subquery("agg")
        )

        ps_open = aliased(ps1m, name="ps_open")
        ps_close = aliased(ps1m, name="ps_close")

        stmt = (
            select(
                agg_sq.c.exchange_instrument_id.label("exchange_instrument_id"),
                # literal(start_dt).label("ts_open"),  # 1h candle start is bucket_start
                ps_open.open.label("open"),
                agg_sq.c.high.label("high"),
                agg_sq.c.low.label("low"),
                ps_close.close.label("close"),
                agg_sq.c.volume.label("volume"),
            )
            .join(
                ps_open,
                (ps_open.exchange_instrument_id == agg_sq.c.exchange_instrument_id)
                & (ps_open.ts_open == agg_sq.c.ts_open_min),
            )
            .join(
                ps_close,
                (ps_close.exchange_instrument_id == agg_sq.c.exchange_instrument_id)
                & (ps_close.ts_open == agg_sq.c.ts_open_max),
            )
        )

        rows = self._db.execute(stmt).all()

        return [
            MarketDTO.PriceSnapshotCreate(
                exchange_instrument_id=r.exchange_instrument_id,
                ts_open=start_dt,
                open=r.open,
                high=r.high,
                low=r.low,
                close=r.close,
                volume=r.volume,
                updated_at=utcnow(),
            )
            for r in rows
        ]

    def list_snapshot_1d_agg(
        self,
        start_dt: datetime,
        end_dt: datetime,
    ) -> list[MarketDTO.PriceSnapshotCreate]:
        agg_sq = (
            select(
                ps1h.exchange_instrument_id.label("exchange_instrument_id"),
                func.max(ps1h.high).label("high"),
                func.min(ps1h.low).label("low"),
                func.sum(ps1h.volume).label("volume"),
                func.min(ps1h.ts_open).label("ts_open_min"),
                func.max(ps1h.ts_open).label("ts_open_max"),
            )
            .where(ps1h.ts_open >= start_dt, ps1h.ts_open < end_dt)
            .group_by(ps1h.exchange_instrument_id)
            .subquery("agg")
        )

        ps_open = aliased(ps1h, name="ps_open")
        ps_close = aliased(ps1h, name="ps_close")

        stmt = (
            select(
                agg_sq.c.exchange_instrument_id.label("exchange_instrument_id"),
                # literal(start_dt).label("ts_open"),  # 1h candle start is bucket_start
                ps_open.open.label("open"),
                agg_sq.c.high.label("high"),
                agg_sq.c.low.label("low"),
                ps_close.close.label("close"),
                agg_sq.c.volume.label("volume"),
            )
            .join(
                ps_open,
                (ps_open.exchange_instrument_id == agg_sq.c.exchange_instrument_id)
                & (ps_open.ts_open == agg_sq.c.ts_open_min),
            )
            .join(
                ps_close,
                (ps_close.exchange_instrument_id == agg_sq.c.exchange_instrument_id)
                & (ps_close.ts_open == agg_sq.c.ts_open_max),
            )
        )

        rows = self._db.execute(stmt).all()

        return [
            MarketDTO.PriceSnapshotCreate(
                exchange_instrument_id=r.exchange_instrument_id,
                ts_open=start_dt,
                open=r.open,
                high=r.high,
                low=r.low,
                close=r.close,
                volume=r.volume,
                updated_at=utcnow(),
            )
            for r in rows
        ]

    # ---------------------------- add ----------------------------------------------

    def add_exchange_instruments(
        self, exchange_instruments: list[MarketDTO.ExchangeInstrumentSync]
    ) -> None:
        if not exchange_instruments:
            return

        rows = [
            ExchangeInstrumentModel(
                exchange_id=ei.exchange_id,
                exchange_symbol=ei.exchange_symbol,
                base_asset_id=ei.base_asset_id,
                quote_asset_id=ei.quote_asset_id,
                price_precision=ei.price_precision,
                qty_precision=ei.qty_precision,
                min_notional=ei.min_notional,
                updated_at=ei.updated_at,
                is_active=ei.is_active,
            )
            for ei in exchange_instruments
        ]
        self._db.add_all(rows)

    def upsert_exchange_instrument_tickers(
        self,
        rows: list[MarketDTO.ExchangeInstrumentTickerCreate],
        *,
        chunk_size: int = 1000,
    ) -> None:
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            values = [to_row_dict(x) for x in chunk]

            stmt = mysql_insert(eit).values(values)
            stmt = stmt.on_duplicate_key_update(
                open_price=stmt.inserted.open_price,
                close_price=stmt.inserted.close_price,
                high_24h=stmt.inserted.high_24h,
                low_24h=stmt.inserted.low_24h,
                volume_24h=stmt.inserted.volume_24h,
                price_change_24h=stmt.inserted.price_change_24h,
                price_change_rate_24h=stmt.inserted.price_change_rate_24h,
                normalized_price=stmt.inserted.normalized_price,
                normalized_volume=stmt.inserted.normalized_volume,
                updated_at=func.utc_timestamp(),
            )

            self._db.execute(stmt)

    def upsert_exchange_instruments(
        self, exchange_instruments: list[MarketDTO.ExchangeInstrumentSync]
    ) -> int:
        if not exchange_instruments:
            return 0

        total = 0
        CHUNK = 1000

        for i in range(0, len(exchange_instruments), CHUNK):
            chunk = exchange_instruments[i : i + CHUNK]

            values = [
                {
                    "exchange_id": x.exchange_id,
                    "exchange_symbol": x.exchange_symbol,
                    "base_asset_id": x.base_asset_id,
                    "quote_asset_id": x.quote_asset_id,
                    "tick_size": x.tick_size,
                    "price_precision": x.price_precision,
                    "qty_precision": x.qty_precision,
                    "min_notional": x.min_notional,
                    "is_active": x.is_active,
                    "updated_at": x.updated_at,
                }
                for x in chunk
            ]

            stmt = mysql_insert(ei).values(values)

            stmt = stmt.on_duplicate_key_update(
                exchange_symbol=stmt.inserted.exchange_symbol,
                tick_size=stmt.inserted.tick_size,
                price_precision=stmt.inserted.price_precision,
                qty_precision=stmt.inserted.qty_precision,
                min_notional=stmt.inserted.min_notional,
                is_active=stmt.inserted.is_active,
                updated_at=stmt.inserted.updated_at,
                # deleted_at=None # soft delete 살릴거면
            )

            result = self._db.execute(stmt)
            rowcount = result.rowcount or 0
            total += rowcount

        return total

    def upsert_exchange_instruments_by_pairs(
        self,
        exchange_id: int,
        pairs: list[tuple[int, int]],
        is_active: bool,
        updated_at: datetime,
    ) -> int:
        if not pairs:
            return 0
        total = 0

        # MySQL 튜플 IN은 너무 길면 부담이라 배치로 끊는 게 안전
        CHUNK = 1000

        for i in range(0, len(pairs), CHUNK):
            chunk = pairs[i : i + CHUNK]

            stmt = (
                update(ei)
                .where(
                    ei.exchange_id == exchange_id,
                    ei.deleted_at.is_(None),
                    tuple_(
                        ei.base_asset_id,
                        ei.quote_asset_id,
                    ).in_(chunk),
                )
                .values(
                    is_active=is_active,
                    updated_at=updated_at,
                )
            )

            result = cast(CursorResult, self._db.execute(stmt))

            # rowcount는 DB/드라이버에 따라 -1일 수 있음. 그래도 참고값으로 누적.
            rowcount = result.rowcount or 0
            if rowcount > 0:
                total += rowcount

        return total

    def upsert_snapshot_1m(
        self, row: MarketDTO.PriceSnapshotCreate
    ) -> Tuple[int, bool]:
        return self._upsert_snapshot(PriceSnapshot1mModel, row)

    def upsert_snapshot_1h(
        self, row: MarketDTO.PriceSnapshotCreate
    ) -> Tuple[int, bool]:
        return self._upsert_snapshot(PriceSnapshot1hModel, row)

    def upsert_snapshot_1d(
        self, row: MarketDTO.PriceSnapshotCreate
    ) -> Tuple[int, bool]:
        return self._upsert_snapshot(PriceSnapshot1dModel, row)

    def _upsert_snapshot(
        self, model, row: MarketDTO.PriceSnapshotCreate
    ) -> Tuple[int, bool]:
        row_dict = to_row_dict(row)
        stmt = mysql_insert(model).values(**row_dict)
        stmt = stmt.on_duplicate_key_update(
            id=func.last_insert_id(
                model.id
            ),  # 필요하면 model.__table__.c.id 로 써도 OK
            open=stmt.inserted.open,
            high=stmt.inserted.high,
            low=stmt.inserted.low,
            close=stmt.inserted.close,
            volume=stmt.inserted.volume,
        )
        result = cast(CursorResult, self._db.execute(stmt))
        # rowcount:
        # 1 = insert
        # 2 = duplicate update
        # 0 = duplicate인데 같은 값이라 실제 변경 없음
        created = result.rowcount == 1
        _id = int(result.lastrowid)  # insert/duplicate 모두 PK 반환
        return _id, created

    def upsert_snapshots_1m(
        self,
        rows: list[MarketDTO.PriceSnapshotCreate],
        *,
        chunk_size: int = 1000,
    ) -> None:

        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            values = [to_row_dict(x) for x in chunk]

            stmt = mysql_insert(PriceSnapshot1mModel).values(values)
            stmt = stmt.on_duplicate_key_update(
                # 기존 패턴 유지
                id=func.last_insert_id(PriceSnapshot1mModel.id),
                open=stmt.inserted.open,
                high=stmt.inserted.high,
                low=stmt.inserted.low,
                close=stmt.inserted.close,
                volume=stmt.inserted.volume,
                updated_at=stmt.inserted.updated_at,
            )

            self._db.execute(stmt)

    def upsert_snapshots_1h(
        self,
        rows: list[MarketDTO.PriceSnapshotCreate],
        *,
        chunk_size: int = 1000,
    ) -> None:
        tbl = PriceSnapshot1hModel.__table__
        skip_update = {"id", "exchange_instrument_id", "ts_open"}

        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            values = [to_row_dict(r) for r in chunk]
            stmt = mysql_insert(PriceSnapshot1hModel).values(values)

            update_cols = {
                c.name: stmt.inserted[c.name]
                for c in tbl.c
                if c.name not in skip_update
            }
            stmt = stmt.on_duplicate_key_update(**update_cols)

            self._db.execute(stmt)

    def upsert_snapshots_1d(
        self,
        rows: list[MarketDTO.PriceSnapshotCreate],
        *,
        chunk_size: int = 1000,
    ) -> None:
        tbl = PriceSnapshot1dModel.__table__
        skip_update = {"id", "exchange_instrument_id", "ts_open"}

        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            values = [to_row_dict(r) for r in chunk]
            stmt = mysql_insert(PriceSnapshot1dModel).values(values)

            update_cols = {
                c.name: stmt.inserted[c.name]
                for c in tbl.c
                if c.name not in skip_update
            }
            stmt = stmt.on_duplicate_key_update(**update_cols)

            self._db.execute(stmt)

    # ---------------------------------------------------------------------------------
    def seed_snapshots(self, *, interval: str, chunk: list):
        table_map = {
            "1m": PriceSnapshot1mModel,
            "1h": PriceSnapshot1hModel,
            "1d": PriceSnapshot1dModel,
        }
        Model = table_map[interval]

        stmt = insert(Model)
        self._db.execute(stmt, chunk)
