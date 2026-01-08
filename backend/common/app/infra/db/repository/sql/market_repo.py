from typing import Iterable, Sequence, Tuple
from sqlalchemy import insert, select, and_, asc, desc, func
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
from app.domain import MarketDTO
from datetime import datetime
from ..protocol.market_repo import MarketRepo


class SqlMarketRepo(MarketRepo):
    def __init__(self, db: DbSession):
        self._db = db

    def get_by_exchange_instrument_id(
        self, *, exchange_instrumen_id: int
    ) -> MarketDTO.ExchangeInstrument:
        ei = ExchangeInstrumentModel
        stmt = select(ei).where(
            and_(ei.is_deleted.is_(False), ei.id == exchange_instrumen_id)
        )
        return self._db.execute(stmt).scalar_one_or_none()

    # Meta
    def list_exchanges_by_filter(
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

    def list_exchange_instruments_by_filter(
        self,
        *,
        exchange_id: int | None = None,
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
                b.symbol.label("base_symbol"),
                q.symbol.label("quote_symbol"),
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
        if exchange_id is not None:
            stmt = stmt.where(ei.exchange_id == exchange_id)

        rows = self._db.execute(stmt).mappings().all()

        return [MarketDTO.MappingItem(**row) for row in rows]

    def list_mappings_exchange_id(
        self, *, exchange_id: int | None = None
    ) -> list[MarketDTO.MappingItem]:
        ei = ExchangeInstrumentModel

        stmt = select(ei.exchange_id, ei.base_asset_id, ei.quote_asset_id)
        if exchange_id is not None:
            stmt = stmt.where(ei.exchange_id == exchange_id)

        rows = self._db.execute(stmt).mappings().all()

        return [MarketDTO.MappingItem(**row) for row in rows]

    # 공통 빌더
    def _list_candles_by_filter(
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
    def list_1m_by_filter(
        self,
        *,
        exchange_instrument_id: int,
        cursor: datetime | None,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        asc_order: bool,
    ) -> list[MarketDTO.CandleBase]:
        return self._list_candles_by_filter(
            PriceSnapshot1mModel,
            exchange_instrument_id=exchange_instrument_id,
            cursor=cursor,
            start=start,
            end=end,
            limit=limit,
            asc_order=asc_order,
        )

    def list_1h_by_filter(
        self,
        *,
        exchange_instrument_id: int,
        cursor: datetime | None,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        asc_order: bool,
    ) -> list[MarketDTO.CandleBase]:
        return self._list_candles_by_filter(
            PriceSnapshot1hModel,
            exchange_instrument_id=exchange_instrument_id,
            cursor=cursor,
            start=start,
            end=end,
            limit=limit,
            asc_order=asc_order,
        )

    def list_1d_by_filter(
        self,
        *,
        exchange_instrument_id: int,
        cursor: datetime | None,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        asc_order: bool,
    ) -> list[MarketDTO.CandleBase]:
        return self._list_candles_by_filter(
            PriceSnapshot1dModel,
            exchange_instrument_id=exchange_instrument_id,
            cursor=cursor,
            start=start,
            end=end,
            limit=limit,
            asc_order=asc_order,
        )

    # ---------------------------- add ----------------------------------------------
    def upsert_1m(self, row: dict) -> Tuple[int, bool]:
        return self._upsert_one_mysql(PriceSnapshot1mModel, row)

    def upsert_1h(self, row: dict) -> Tuple[int, bool]:
        return self._upsert_one_mysql(PriceSnapshot1hModel, row)

    def upsert_1d(self, row: dict) -> Tuple[int, bool]:
        return self._upsert_one_mysql(PriceSnapshot1dModel, row)

    def _upsert_one_mysql(self, model, row: dict) -> Tuple[int, bool]:
        stmt = mysql_insert(model).values(**row)
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

    def get_symbols(self, exchange_instrument_id: int) -> MarketDTO.MappingItem:
        ei = ExchangeInstrumentModel
        b = aliased(InstrumentModel)
        q = aliased(InstrumentModel)

        stmt = (
            select(
                ei.id.label("id"),
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
