from typing import Sequence
from sqlalchemy import delete, select, func, and_, asc, desc
from sqlalchemy.orm import aliased, Session as DbSession
from app.domain import WatchlistDTO
from app.infra.db.model import (
    WatchlistItemModel,
    ExchangeInstrumentModel,
    InstrumentModel,
)
from ..protocol.watchlist_repo import WatchlistRepo


class SqlWatchlistRepo(WatchlistRepo):
    def __init__(self, db: DbSession):
        self._db = db

    def add_item(
        self, *, user_id: int, exchange_instrument_id: int, sort_order: int
    ) -> WatchlistDTO.WatchlistItem:
        row = WatchlistItemModel(
            user_id=user_id,
            exchange_instrument_id=exchange_instrument_id,
            sort_order=sort_order,
        )
        self._db.add(row)
        self._db.flush()  # id 채우기
        return row.to_dto()

    def list_items_by_filter(
        self, *, user_id: int, limit: int, offset: int, is_asc: bool
    ) -> Sequence[WatchlistDTO.WatchlistItem]:
        order = asc if is_asc else desc
        stmt = (
            select(WatchlistItemModel)
            .where(and_(WatchlistItemModel.user_id == user_id))
            .order_by(order(WatchlistItemModel.sort_order), desc(WatchlistItemModel.id))
            .limit(limit)
            .offset(offset)
        )
        rows = self._db.execute(stmt).scalars().all()
        return [row.to_dto() for row in rows]

    def exists(
        self, *, user_id: int, exchange_instrument_id: int
    ) -> WatchlistDTO.WatchlistItem | None:
        stmt = select(func.count(WatchlistItemModel.id)).where(
            and_(
                WatchlistItemModel.user_id == user_id,
                WatchlistItemModel.exchange_instrument_id == exchange_instrument_id,
            )
        )

        model = self._db.execute(stmt).scalar_one_or_none()
        return model.to_dto() if model else None

    def get_next_sort(self, *, user_id: int) -> int:
        stmt = select(func.coalesce(func.max(WatchlistItemModel.sort_order), 0)).where(
            and_(WatchlistItemModel.user_id == user_id)
        )
        return int(self._db.execute(stmt).scalar_one()) + 1

    def delete_item(self, *, user_id: int, exchange_instrument_id: int) -> None:
        stmt = delete(WatchlistItemModel).where(
            WatchlistItemModel.user_id == user_id,
            WatchlistItemModel.exchange_instrument_id == exchange_instrument_id,
        )

        self._db.execute(stmt)
