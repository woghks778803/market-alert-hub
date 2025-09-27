from typing import Sequence, Tuple
from sqlalchemy import select, func, and_, asc, desc
from sqlalchemy.orm import aliased, Session as DbSession
from app.infra.db.model import (
    WatchlistItemModel, 
    ExchangeInstrumentModel, 
    InstrumentModel
)

class SqlWatchlistRepo:
    def __init__(self, db: DbSession):
        self._db = db

    def list(self, *, user_id: int, limit: int, offset: int, is_asc: bool) -> Sequence[WatchlistItemModel]:
        order = asc if is_asc else desc
        stmt = (
            select(WatchlistItemModel)
            .where(and_(WatchlistItemModel.user_id == user_id, WatchlistItemModel.is_valid == True))
            .order_by(order(WatchlistItemModel.sort_order), desc(WatchlistItemModel.id))
            .limit(limit)
            .offset(offset)
        )
        return self._db.execute(stmt).scalars().all()

    def exists(self, *, user_id: int, exchange_instrument_id: int) -> bool:
        stmt = (
            select(func.count(WatchlistItemModel.id))
            .where(
                and_(
                    WatchlistItemModel.user_id == user_id,
                    WatchlistItemModel.exchange_instrument_id == exchange_instrument_id,
                    WatchlistItemModel.is_valid == True,
                )
            )
        )
        return self._db.execute(stmt).scalar_one() > 0

    def mapping_exists(self, *, exchange_instrument_id: int) -> bool:
        stmt = select(func.count(ExchangeInstrumentModel.id)).where(
            and_(
                ExchangeInstrumentModel.id == exchange_instrument_id,
            )
        )
        return self._db.execute(stmt).scalar_one() > 0

    def next_sort_order(self, *, user_id: int) -> int:
        stmt = select(func.coalesce(func.max(WatchlistItemModel.sort_order), 0)).where(
            and_(WatchlistItemModel.user_id == user_id, WatchlistItemModel.is_valid == True)
        )
        return int(self._db.execute(stmt).scalar_one()) + 1

    def create(self, *, user_id: int, exchange_instrument_id: int, sort_order: int) -> WatchlistItemModel:
        row = WatchlistItemModel(
            user_id=user_id,
            exchange_instrument_id=exchange_instrument_id,
            sort_order=sort_order,
            is_valid=True,
        )
        self._db.add(row)
        self._db.flush()  # id 채우기
        return row

    def get_by_id(self, *, item_id: int, user_id: int) -> WatchlistItemModel:
        stmt = (
            select(WatchlistItemModel)
            .where(and_(WatchlistItemModel.id == item_id, WatchlistItemModel.user_id == user_id))
            .limit(1)
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def pick_display_fields(self, row: WatchlistItemModel) -> Tuple[str, str, str]:
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

        if row.exchange_instrument_id is not None:
            stmt = stmt.where(ei.id == row.exchange_instrument_id)

        row = self._db.execute(stmt).one_or_none()
        return row.exchange_symbol, row.base_symbol, row.quote_symbol
