from typing import Callable
from datetime import datetime, timezone
from app.api.schema.market import ExchangeRead, InstrumentRead, MappingItem, LatestPriceRead, Candle1mRead
from app.domain.errors import NotFoundError  # 네 프로젝트의 404 에러 클래스 사용
from app.service.uow import UnitOfWork

class MarketService:
    def __init__(
        self, 
        *,
        uow_factory: Callable[[], UnitOfWork],
    ) -> None:
        self._uow_factory = uow_factory

    # Meta
    def list_exchanges(self, *, limit: int, offset: int) -> list[ExchangeRead]:
        with self._uow_factory() as uow:
            
            rows = uow.markets.list_exchanges(limit=limit, offset=offset)
            return [ExchangeRead.model_validate(r) for r in rows]

    def list_instruments(self, *, exchange_id: int | None, limit: int, offset: int) -> list[InstrumentRead]:
        with self._uow_factory() as uow:
            rows = uow.markets.list_instruments(exchange_id=exchange_id, limit=limit, offset=offset)
            return [InstrumentRead(id=r.id, code=r.symbol, name=f"{r.base_asset}/{r.quote_asset}") for r in rows]

    def list_mapping(self, *, exchange_id: int | None) -> list[MappingItem]:
        with self._uow_factory() as uow:
            rows = uow.markets.list_mapping(exchange_id=exchange_id)
            return [MappingItem(exchange_id=ex, instrument_id=ins) for (ex, ins) in rows]

    # Prices
    def get_latest(self, *, exchange_id: int, instrument_id: int) -> LatestPriceRead:
        with self._uow_factory() as uow:
            row = uow.markets.get_latest(exchange_id=exchange_id, instrument_id=instrument_id)
            if not row:
                raise NotFoundError("Latest price not found", target="instrument_id")
            return LatestPriceRead(
                exchange_id=row.exchange_id,
                instrument_id=row.instrument_id,
                price=row.last_price,
                as_of=row.ts,  # 컬럼명이 다르면 맞춰서 수정
            )

    def list_candles_1m(
        self, *,
        exchange_id: int,
        instrument_id: int,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        asc_order: bool = True,
    ) -> list[Candle1mRead]:
        with self._uow_factory() as uow:
            rows = uow.markets.list_candles_1m(
                exchange_id=exchange_id,
                instrument_id=instrument_id,
                start=start,
                end=end,
                limit=limit,
                asc_order=asc_order,
            )
            return [
                Candle1mRead(
                    exchange_id=r.exchange_id,
                    instrument_id=r.instrument_id,
                    bucket=r.bucket_minute,
                    open=r.open,
                    high=r.high,
                    low=r.low,
                    close=r.close,
                    volume=getattr(r, "volume", None),
                ) for r in rows
            ]
