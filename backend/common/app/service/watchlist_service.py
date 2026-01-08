from typing import List, Callable
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import ConflictError, ValidationAppError
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

                symbols = uow.markets.get_symbols(row.exchange_instrument_id)
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
                        base_symbol=symbols.base_symbol,
                        quote_symbol=symbols.quote_symbol,
                        exchange_symbol=symbols.exchange_symbol,
                        sort_order=row.sort_order,
                        created_at=row.created_at,
                    )
                )
            return result

    def create_item(
        self, *, user_id: int, dto: WatchlistDTO.WatchlistCreate
    ) -> WatchlistDTO.WatchlistItemRead:
        with self._uow_factory() as uow:
            if not uow.watchlists.mapping_exists(
                exchange_instrument_id=dto.exchange_instrument_id
            ):
                raise ValidationAppError(
                    "Mapping not found", target="exchange_instrument_id"
                )

            if uow.watchlists.exists(
                user_id=user_id, exchange_instrument_id=dto.exchange_instrument_id
            ):
                raise ConflictError(
                    "Already in watchlist", target="user_id,exchange_instrument_id"
                )

            sort_order = (
                dto.sort_order
                if dto.sort_order is not None
                else uow.watchlists.get_next_sort(user_id=user_id)
            )
            row = uow.watchlists.add_item(
                user_id=user_id,
                exchange_instrument_id=dto.exchange_instrument_id,
                sort_order=sort_order,
            )
            symbols = uow.markets.get_symbols(row.exchange_instrument_id)

            uow.commit()
            return WatchlistDTO.WatchlistItemRead(
                id=row.id,
                exchange_instrument_id=row.exchange_instrument_id,
                base_symbol=symbols.base_symbol,
                quote_symbol=symbols.quote_symbol,
                exchange_symbol=symbols.exchange_symbol,
                sort_order=row.sort_order,
                created_at=row.created_at,
            )

    def delete_item(self, *, item_id: int, user_id: int) -> None:
        with self._uow_factory() as uow:

            watchlist_items = uow.watchlists.get_item_by_filter(
                item_id=item_id, user_id=user_id
            )
            if hasattr(watchlist_items, "is_deleted"):
                watchlist_items.is_deleted = True
            uow.commit()
