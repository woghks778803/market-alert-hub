from typing import Iterable, Sequence
from sqlalchemy import select, and_, asc, desc
from sqlalchemy.orm import Session as DbSession
from app.infra.db.model import Exchange, Instrument, ExchangeInstrument, PriceLatest, PriceSnapshot1m
from datetime import datetime

class SqlMarketRepo:
    def __init__(self, db: DbSession):
        self._db = db

    # Meta
    def list_exchanges(self, *, limit: int = 100, offset: int = 0) -> Sequence[Exchange]:
        stmt = select(Exchange).where(Exchange.is_valid == True).order_by(asc(Exchange.id)).limit(limit).offset(offset)
        return self._db.execute(stmt).scalars().all()

    def list_instruments(self, *, exchange_id: int | None = None, limit: int = 200, offset: int = 0) -> Sequence[Instrument]:
        stmt = select(Instrument).where(Instrument.is_valid == True)
        if exchange_id:
            # exchange_instruments 조인 기반 필터
            stmt = stmt.join(ExchangeInstrument, ExchangeInstrument.instrument_id == Instrument.id)\
                       .where(ExchangeInstrument.exchange_id == exchange_id)
        stmt = stmt.order_by(asc(Instrument.id)).limit(limit).offset(offset)
        return self._db.execute(stmt).scalars().all()

    def list_mapping(self, *, exchange_id: int | None = None) -> Iterable[tuple[int, int]]:
        stmt = select(ExchangeInstrument.exchange_id, ExchangeInstrument.instrument_id)
        if exchange_id:
            stmt = stmt.where(ExchangeInstrument.exchange_id == exchange_id)
        return self._db.execute(stmt).all()

    # Prices
    def get_latest(self, *, exchange_id: int, instrument_id: int) -> PriceLatest | None:
        stmt = select(PriceLatest).where(
            and_(
                PriceLatest.exchange_id == exchange_id,
                PriceLatest.instrument_id == instrument_id,
            )
        )
        return self._db.execute(stmt).scalars().first()

    def list_candles_1m(
        self, *,
        exchange_id: int,
        instrument_id: int,
        start: datetime | None,
        end: datetime | None,
        limit: int = 500,
        asc_order: bool = True,
    ) -> Sequence[PriceSnapshot1m]:
        stmt = select(PriceSnapshot1m).where(
            and_(
                PriceSnapshot1m.exchange_id == exchange_id,
                PriceSnapshot1m.instrument_id == instrument_id,
            )
        )
        if start:
            stmt = stmt.where(PriceSnapshot1m.bucket_minute >= start)
        if end:
            stmt = stmt.where(PriceSnapshot1m.bucket_minute < end)
        stmt = stmt.order_by(asc(PriceSnapshot1m.bucket_minute) if asc_order else desc(PriceSnapshot1m.bucket_minute)).limit(limit)
        return self._db.execute(stmt).scalars().all()
