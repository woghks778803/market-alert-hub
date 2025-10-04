from typing import List, Callable
from app.service.uow import UnitOfWork
from app.domain import WatchlistDTO, ConflictError, ValidationAppError

class WatchlistService:
    def __init__(
            self,
            *, 
            uow_factory: Callable[[], UnitOfWork]
        ):
        self._uow_factory = uow_factory

    def list(self, *, user_id: int, limit: int, offset: int, is_asc: bool) -> List[WatchlistDTO.WatchlistItemRead]:
        with self._uow_factory() as uow:
            rows = uow.watchlists.list(user_id=user_id, limit=limit, offset=offset, is_asc=is_asc)
            result: List[WatchlistDTO.WatchlistItemRead] = []
            for row in rows:
                exchange_symbol, base_symbol, quote_symbol = uow.markets.get_symbols(row.exchange_instrument_id)
                result.append(
                    WatchlistDTO.WatchlistItemRead(
                        id=row.id,
                        exchange_instrument_id=row.exchange_instrument_id,
                        base_symbol=base_symbol,
                        quote_symbol=quote_symbol,
                        exchange_symbol=exchange_symbol,
                        sort_order=row.sort_order,
                        created_at=row.created_at,
                    )
                )
            return result

    def create(self, *, user_id: int, data: WatchlistDTO.WatchlistCreate) -> WatchlistDTO.WatchlistItemRead:
        with self._uow_factory() as uow:
            if not uow.watchlists.mapping_exists(
                exchange_instrument_id=data.exchange_instrument_id
            ):
                raise ValidationAppError("Mapping not found", target="exchange_instrument_id")

            if uow.watchlists.exists(
                user_id=user_id, exchange_instrument_id=data.exchange_instrument_id
            ):
                raise ConflictError("Already in watchlist", target="user_id,exchange_instrument_id")

            sort_order = data.sort_order if data.sort_order is not None else uow.watchlists.next_sort_order(user_id=user_id)
            row = uow.watchlists.create(
                user_id=user_id,
                exchange_instrument_id=data.exchange_instrument_id,
                sort_order=sort_order,
            )
            exchange_symbol, base_symbol, quote_symbol = uow.markets.get_symbols(row.exchange_instrument_id)
            uow.commit()
            return WatchlistDTO.WatchlistItemRead(
                id=row.id,
                exchange_instrument_id=row.exchange_instrument_id,
                base_symbol=base_symbol,
                quote_symbol=quote_symbol,
                exchange_symbol=exchange_symbol,
                sort_order=row.sort_order,
                created_at=row.created_at,
            )

    def delete(self, *, item_id: int, user_id: int) -> None:
        with self._uow_factory() as uow:
            
            watchlist_items = uow.watchlists.get_by_id(item_id=item_id, user_id=user_id)
            if hasattr(watchlist_items, "is_deleted"):
                watchlist_items.is_deleted = True
            uow.commit()


