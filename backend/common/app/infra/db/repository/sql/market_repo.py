from cProfile import label
from decimal import Decimal
from typing import Iterable, Sequence, Tuple
from sqlalchemy import update, insert, select, and_, asc, desc, func, tuple_
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import aliased, Session as DbSession
from app.infra.db.model import (
    ExchangeModel,
    InstrumentModel,
    ExchangeInstrumentModel,
    PriceSnapshot1mModel,
    PriceSnapshot1hModel,
    PriceSnapshot1dModel,
)
from app.core.util.datetime import utcnow
from app.domain import MarketDTO
from datetime import datetime
from ..protocol.market_repo import MarketRepo
from app.infra.db.utils import to_row_dict


class SqlMarketRepo(MarketRepo):
    def __init__(self, db: DbSession):
        self._db = db

    def get_exchange_by_filter(
        self,
        id: int | None = None,
        code: str | None = None,
        is_active: bool = True,
        is_delete: bool = False,
    ) -> MarketDTO.Exchange | None:
        e = ExchangeModel
        stmt = select(e).where(
            and_(
                e.is_active.is_(is_active),
                e.is_deleted.is_(is_delete),
            )
        )

        if id is not None:
            stmt = stmt.where(e.id == id)
        if code is not None:
            stmt = stmt.where(e.code == code)

        exchange = self._db.execute(stmt).scalars().one_or_none()
        if exchange is None:
            return None
        return exchange.to_dto()

    def get_by_exchange_instrument_filter(
        self,
        *,
        exchange_instrument_id: int,
        is_active: bool = True,
        is_delete: bool = False,
    ) -> MarketDTO.ExchangeInstrument | None:
        ei = ExchangeInstrumentModel
        stmt = select(ei).where(
            and_(
                ei.is_deleted.is_(is_delete),
                ei.is_active.is_(is_active),
                ei.id == exchange_instrument_id,
            )
        )
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
        ps_1m = PriceSnapshot1mModel
        ids = [int(x) for x in exchange_instrument_ids]
        if not ids:
            return {}

        subq = (
            select(
                ps_1m.exchange_instrument_id,
                func.max(ps_1m.ts_open).label("max_ts_open"),
            )
            .where(ps_1m.exchange_instrument_id.in_(ids))
            .group_by(ps_1m.exchange_instrument_id)
            .subquery()
        )

        stmt = select(ps_1m).join(
            subq,
            and_(
                ps_1m.exchange_instrument_id == subq.c.exchange_instrument_id,
                ps_1m.ts_open == subq.c.max_ts_open,
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
        is_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[MarketDTO.Exchange]:
        stmt = (
            select(ExchangeModel)
            .where(
                and_(
                    ExchangeModel.is_deleted.is_(is_deleted),
                    ExchangeModel.is_active.is_(is_active),
                )
            )
            .order_by(asc(ExchangeModel.id))
            .limit(limit)
            .offset(offset)
        )
        rows = self._db.execute(stmt).scalars().all()

        return [row.to_dto() for row in rows]

    def list_instrument_by_filter(
        self,
        *,
        is_active: bool | None = None,
        is_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[MarketDTO.Instrument]:
        stmt = (
            select(InstrumentModel)
            .where(
                InstrumentModel.is_deleted.is_(is_deleted),
            )
            .order_by(asc(InstrumentModel.id))
            .limit(limit)
            .offset(offset)
        )

        if is_active is not None:
            stmt.where(InstrumentModel.is_active == is_active)

        rows = self._db.execute(stmt).scalars().all()

        return [row.to_dto() for row in rows]

    def list_exchange_instrument_by_filter(
        self,
        *,
        exchange_id: int | None = None,
        is_active: bool | None = None,
        is_deleted: bool = False,
        limit: int = 200,
        offset: int = 0,
    ) -> list[MarketDTO.MappingItem]:
        ei = ExchangeInstrumentModel
        e = ExchangeModel
        b = aliased(InstrumentModel)
        q = aliased(InstrumentModel)

        stmt = (
            select(
                ei.id.label("id"),
                ei.exchange_symbol.label("exchange_symbol"),
                ei.base_asset_id,
                ei.quote_asset_id,
                b.symbol.label("base_symbol"),
                q.symbol.label("quote_symbol"),
                e.id.label("exchange_id"),
                e.name.label("exchange_name"),
            )
            .select_from(ExchangeInstrumentModel)
            .join(e, ei.exchange)
            .join(b, ei.base_asset)
            .join(q, ei.quote_asset)
            .where(
                and_(
                    ei.is_deleted.is_(is_deleted),
                    b.is_deleted.is_(is_deleted),
                    q.is_deleted.is_(is_deleted),
                )
            )
            .order_by(asc(ei.exchange_symbol))
            .limit(limit)
            .offset(offset)
        )
        if is_active is not None:
            stmt = stmt.where(ei.is_active == is_active)
        if exchange_id is not None:
            stmt = stmt.where(ei.exchange_id == exchange_id)

        rows = self._db.execute(stmt).mappings().all()

        return [MarketDTO.MappingItem(**row) for row in rows]

    def list_mappings_exchange_id(
        self, *, exchange_id: int | None = None
    ) -> list[MarketDTO.MappingItem]:
        ei = ExchangeInstrumentModel

        stmt = select(
            ei.id.label("id"), ei.exchange_id, ei.base_asset_id, ei.quote_asset_id
        )
        if exchange_id is not None:
            stmt = stmt.where(ei.exchange_id == exchange_id)

        rows = self._db.execute(stmt).mappings().all()

        return [MarketDTO.MappingItem(**row) for row in rows]

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
    ) -> list[MarketDTO.CandleBase]:
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
            MarketDTO.CandleBase(
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
    ) -> list[MarketDTO.CandleBase]:
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
    ) -> list[MarketDTO.CandleBase]:
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
    ) -> list[MarketDTO.CandleBase]:
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
        PS1m = PriceSnapshot1mModel

        agg_sq = (
            select(
                PS1m.exchange_instrument_id.label("exchange_instrument_id"),
                func.max(PS1m.high).label("high"),
                func.min(PS1m.low).label("low"),
                func.sum(PS1m.volume).label("volume"),
                func.min(PS1m.ts_open).label("ts_open_min"),
                func.max(PS1m.ts_open).label("ts_open_max"),
            )
            .where(PS1m.ts_open >= start_dt, PS1m.ts_open < end_dt)
            .group_by(PS1m.exchange_instrument_id)
            .subquery("agg")
        )

        ps_open = aliased(PS1m, name="ps_open")
        ps_close = aliased(PS1m, name="ps_close")

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
        PS1h = PriceSnapshot1hModel

        agg_sq = (
            select(
                PS1h.exchange_instrument_id.label("exchange_instrument_id"),
                func.max(PS1h.high).label("high"),
                func.min(PS1h.low).label("low"),
                func.sum(PS1h.volume).label("volume"),
                func.min(PS1h.ts_open).label("ts_open_min"),
                func.max(PS1h.ts_open).label("ts_open_max"),
            )
            .where(PS1h.ts_open >= start_dt, PS1h.ts_open < end_dt)
            .group_by(PS1h.exchange_instrument_id)
            .subquery("agg")
        )

        ps_open = aliased(PS1h, name="ps_open")
        ps_close = aliased(PS1h, name="ps_close")

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
        self, exchange_instruments: list[MarketDTO.ExchangeInstrumentCreate]
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
                is_deleted=ei.is_deleted,
            )
            for ei in exchange_instruments
        ]
        self._db.add_all(rows)

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
        ei = ExchangeInstrumentModel
        # MySQL 튜플 IN은 너무 길면 부담이라 배치로 끊는 게 안전
        CHUNK = 1000

        for i in range(0, len(pairs), CHUNK):
            chunk = pairs[i : i + CHUNK]

            stmt = (
                update(ei)
                .where(
                    ei.exchange_id == exchange_id,
                    ei.is_deleted.is_(False),
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

            result = self._db.execute(stmt)
            # rowcount는 DB/드라이버에 따라 -1일 수 있음. 그래도 참고값으로 누적.
            if result.rowcount and result.rowcount > 0:
                total += result.rowcount

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
        res = self._db.execute(stmt)
        # rowcount: 1=insert, 2=update, 0=no-op (같은 값으로 업데이트)
        created = res.rowcount == 1
        _id = int(res.lastrowid)  # insert/duplicate 모두 PK 반환
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

    def get_symbol(self, exchange_instrument_id: int) -> MarketDTO.MappingItem:
        ei = ExchangeInstrumentModel
        b = aliased(InstrumentModel)
        q = aliased(InstrumentModel)

        stmt = (
            select(
                ei.id.label("id"),
                ei.base_asset_id,
                ei.quote_asset_id,
                ei.exchange_symbol.label("exchange_symbol"),
                b.symbol.label("base_symbol"),
                q.symbol.label("quote_symbol"),
            )
            .select_from(ExchangeInstrumentModel)
            .join(b, ei.base_asset)
            .join(q, ei.quote_asset)
            .limit(1)
        )

        stmt = stmt.where(ei.id == exchange_instrument_id)

        row = self._db.execute(stmt).mappings().one()
        return MarketDTO.MappingItem(**row)
