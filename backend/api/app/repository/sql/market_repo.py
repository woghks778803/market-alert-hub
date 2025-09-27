from typing import Iterable, Sequence
from sqlalchemy import select, and_, asc, desc
from sqlalchemy.orm import aliased, Session as DbSession
from app.infra.db.model import (
    ExchangeModel, InstrumentModel, ExchangeInstrumentModel, 
    PriceSnapshot1mModel, PriceSnapshot1hModel, PriceSnapshot1dModel
)
from app.domain.dto import MarketDTO
from datetime import datetime
from decimal import Decimal


class SqlMarketRepo:
    def __init__(self, db: DbSession):
        self._db = db

    # Meta
    def list_exchanges(self, *, limit: int = 100, offset: int = 0) -> Sequence[ExchangeModel]:
        stmt = select(ExchangeModel).where(ExchangeModel.is_valid == True).order_by(asc(ExchangeModel.id)).limit(limit).offset(offset)
        return self._db.execute(stmt).scalars().all()

    def list_exchange_instruments(self, *, exchange_id: int | None = None, limit: int = 200, offset: int = 0) -> list[MarketDTO.MarketInstrumentBrief]:
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
            .where(ei.is_valid.is_(True))
            .order_by(asc(ei.exchange_symbol))
            .limit(limit).offset(offset)
        )
        if exchange_id is not None:
            stmt = stmt.where(ei.exchange_id == exchange_id)

        rows = self._db.execute(stmt).mappings().all()

        return [MarketDTO.MarketInstrumentBrief(**row) for row in rows]

    def list_mapping(self, *, exchange_id: int | None = None) -> Iterable[tuple[int, int, int]]:
        stmt = select(ExchangeInstrumentModel.exchange_id, ExchangeInstrumentModel.base_asset_id, ExchangeInstrumentModel.quote_asset_id)
        if exchange_id:
            stmt = stmt.where(ExchangeInstrumentModel.exchange_id == exchange_id)
        return self._db.execute(stmt).all()


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
    
    def seed_snapshot(
        self,
        *,
        interval: str,
        exchange_instrument_id: int,
        ts_open: datetime,
        open: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: Decimal,
    ):
        table_map = {
            "1m": PriceSnapshot1mModel,
            "1h": PriceSnapshot1hModel,
            "1d": PriceSnapshot1dModel,
        }
        Model = table_map[interval]

        row = Model(
            exchange_instrument_id=exchange_instrument_id,
            ts_open=ts_open,
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume,
        )
        self._db.add(row)