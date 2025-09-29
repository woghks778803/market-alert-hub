from typing import Iterable, Sequence, Tuple
from sqlalchemy import insert, select, and_, asc, desc, func
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import aliased, Session as DbSession
from app.infra.db.model import (
    ExchangeModel, InstrumentModel, ExchangeInstrumentModel, 
    PriceSnapshot1mModel, PriceSnapshot1hModel, PriceSnapshot1dModel
)
from app.domain import MarketDTO
from datetime import datetime
from decimal import Decimal


class SqlMarketRepo:
    def __init__(self, db: DbSession):
        self._db = db

    # Meta
    def list_exchanges(self, *, limit: int = 100, offset: int = 0) -> Sequence[ExchangeModel]:
        stmt = select(ExchangeModel).where(ExchangeModel.is_valid.is_(True)).order_by(asc(ExchangeModel.id)).limit(limit).offset(offset)
        return self._db.execute(stmt).scalars().all()

    def list_exchange_instruments(self, *, exchange_id: int | None = None, limit: int = 200, offset: int = 0) -> list[MarketDTO.MarketInstrumentItem]:
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
            .where(and_(ei.is_valid.is_(True), b.is_valid.is_(True), q.is_valid.is_(True)))
            .order_by(asc(ei.exchange_symbol))
            .limit(limit).offset(offset)
        )
        if exchange_id is not None:
            stmt = stmt.where(ei.exchange_id == exchange_id)

        rows = self._db.execute(stmt).mappings().all()

        return [MarketDTO.MarketInstrumentItem(**row) for row in rows]

    def list_mapping(self, *, exchange_id: int | None = None) -> list[MarketDTO.MappingItem]:
        ei = ExchangeInstrumentModel

        stmt = select(ei.exchange_id, ei.base_asset_id, ei.quote_asset_id)
        if exchange_id:
            stmt = stmt.where(ei.exchange_id == exchange_id)
        
        rows = self._db.execute(stmt).tuples().all()

        return [MarketDTO.MappingItem(*row) for row in rows]


    # 공통 빌더
    def _list_candles(
        self,
        model,
        *,
        exchange_instrument_id: int,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        asc_order: bool,
    ) -> Sequence:
        conds = [
            model.exchange_instrument_id == exchange_instrument_id,
        ]
        if start is not None:
            conds.append(model.ts_open >= start)
        if end is not None:
            conds.append(model.ts_open < end)

        order_by = asc(model.ts_open) if asc_order else desc(model.ts_open)

        stmt = (
            select(model)
            .where(and_(*conds))
            .order_by(order_by)
            .limit(limit)
        )
        return self._db.execute(stmt).scalars().all()
    
    # 1m/1h/1d 개별 메서드
    def list_candles_1m(
        self, *, exchange_instrument_id: int,
        start: datetime | None, end: datetime | None,
        limit: int, asc_order: bool,
    ):
        return self._list_candles(
            PriceSnapshot1mModel,
            exchange_instrument_id=exchange_instrument_id,
            start=start, end=end, limit=limit, asc_order=asc_order,
        )

    def list_candles_1h(
        self, *, exchange_instrument_id: int,
        start: datetime | None, end: datetime | None,
        limit: int, asc_order: bool,
    ):
        return self._list_candles(
            PriceSnapshot1hModel,
            exchange_instrument_id=exchange_instrument_id,
            start=start, end=end, limit=limit, asc_order=asc_order,
        )

    def list_candles_1d(
        self, *, exchange_instrument_id: int,
        start: datetime | None, end: datetime | None,
        limit: int, asc_order: bool,
    ):
        return self._list_candles(
            PriceSnapshot1dModel,
            exchange_instrument_id=exchange_instrument_id,
            start=start, end=end, limit=limit, asc_order=asc_order,
        )
    
    # ---------------------------- add ----------------------------------------------
    def upsert_one_1m(self, row: dict) -> Tuple[int, bool]:
        return self._upsert_one_mysql(PriceSnapshot1mModel, row)

    def upsert_one_1h(self, row: dict) -> Tuple[int, bool]:
        return self._upsert_one_mysql(PriceSnapshot1hModel, row)

    def upsert_one_1d(self, row: dict) -> Tuple[int, bool]:
        return self._upsert_one_mysql(PriceSnapshot1dModel, row)

    def _upsert_one_mysql(self, model, row: dict) -> Tuple[int, bool]:
        stmt = mysql_insert(model).values(**row)
        stmt = stmt.on_duplicate_key_update(
            id=func.last_insert_id(model.id),       # 필요하면 model.__table__.c.id 로 써도 OK
            open=stmt.inserted.open,
            high=stmt.inserted.high,
            low=stmt.inserted.low,
            close=stmt.inserted.close,
            volume=stmt.inserted.volume,
        )
        res = self._db.execute(stmt)
        # rowcount: 1=insert, 2=update, 0=no-op (같은 값으로 업데이트)
        created = (res.rowcount == 1)
        _id = int(res.lastrowid)  # insert/duplicate 모두 PK 반환
        return _id, created

    # ---------------------------------------------------------------------------------
    def seed_snapshots(
        self,
        *,
        interval: str,
        chunk: list
    ):
        table_map = {
            "1m": PriceSnapshot1mModel,
            "1h": PriceSnapshot1hModel,
            "1d": PriceSnapshot1dModel,
        }
        Model = table_map[interval]

        stmt = insert(Model)
        self._db.execute(stmt, chunk)


    def get_symbols(self, exchange_instrument_id: int) -> MarketDTO.MappingSymbol:
        ei = ExchangeInstrumentModel
        b = aliased(InstrumentModel)
        q = aliased(InstrumentModel)

        stmt = (
            select(
                ei.id.label("id"),
                ei.exchange_symbol.label("exchange_symbol"),
                b.symbol.label("base_symbol"),
                q.symbol.label("quote_symbol")
            )
            .select_from(ExchangeInstrumentModel)
            .join(b, ei.base_asset)
            .join(q, ei.quote_asset)
            .limit(1)
        )

        if exchange_instrument_id is not None:
            stmt = stmt.where(ei.id == exchange_instrument_id)

        row = self._db.execute(stmt).one_or_none()
        
        return MarketDTO.MappingSymbol(
            exchange_symbol=row.exchange_symbol, 
            base_symbol=row.base_symbol, 
            quote_symbol=row.quote_symbol
        )