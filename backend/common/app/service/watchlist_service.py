from typing import List, Callable
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import ConflictError, ValidationAppError, NotFoundError
from app.domain import WatchlistDTO


class WatchlistService:
    def __init__(self, *, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    def list_items_by_filter(
        self, *, user_id: int, limit: int, offset: int, is_asc: bool
    ) -> List[WatchlistDTO.WatchlistItemRead]:
        with self._uow_factory() as uow:
            rows = uow.watchlists.list_items_by_filter(
                user_id=user_id, limit=limit, offset=offset, is_asc=is_asc
            )
            result: List[WatchlistDTO.WatchlistItemRead] = []
            for row in rows:

                symbols = uow.markets.get_symbol(row.exchange_instrument_id)
                if (
                    symbols.base_symbol is None
                    or symbols.quote_symbol is None
                    or symbols.exchange_symbol is None
                ):
                    raise ValidationAppError("Mapping not found", target="symbols")

                result.append(
                    WatchlistDTO.WatchlistItemRead(
                        id=row.id,
                        exchange_instrument_id=row.exchange_instrument_id,
                        sort_order=row.sort_order,
                    )
                )
            return result

    def create_item(
        self, *, user_id: int, exchange_instrument_id: int, sort_order: int | None
    ) -> WatchlistDTO.WatchlistItemRead:
        with self._uow_factory() as uow:

            if not uow.markets.get_by_exchange_instrument_filter(
                exchange_instrument_id=exchange_instrument_id
            ):
                raise NotFoundError("Market not found", target="market")

            if uow.watchlists.exists(
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
