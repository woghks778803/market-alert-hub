from typing import List, Callable
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import ConflictError, ValidationAppError, NotFoundError
from app.domain import WatchlistDTO


class WatchlistService:
    def __init__(self, *, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    def create_item(
        self, *, user_id: int, exchange_instrument_id: int, sort_order: int | None
    ) -> WatchlistDTO.WatchlistItemRead:
        with self._uow_factory() as uow:

            if not uow.markets.get_exchange_instrument_by_filter(
                exchange_instrument_id=exchange_instrument_id
            ):
                raise NotFoundError("Market not found", target="market")

            if uow.watchlists.get_item_by_filter(
                user_id=user_id, exchange_instrument_id=exchange_instrument_id
            ):
                raise ConflictError("Already in watchlist", target="watchlist")

            sort_order = (
                sort_order
                if sort_order is not None
                else uow.watchlists.get_next_sort(user_id=user_id)
            )
            row = uow.watchlists.add_item(
                user_id=user_id,
                exchange_instrument_id=exchange_instrument_id,
                sort_order=sort_order,
            )

            uow.commit()

            return WatchlistDTO.WatchlistItemRead(
                id=row.id,
                exchange_instrument_id=row.exchange_instrument_id,
                sort_order=row.sort_order,
            )

    def delete_item(self, *, exchange_instrument_id: int, user_id: int) -> None:
        with self._uow_factory() as uow:

            uow.watchlists.delete_item(
                exchange_instrument_id=exchange_instrument_id, user_id=user_id
            )

            uow.commit()
