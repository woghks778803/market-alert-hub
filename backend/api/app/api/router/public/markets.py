from datetime import datetime
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_services
from app.service.factory import ServiceFactory
from app.api.schema import MarketSchema
from app.core.constants import CandleBaseInterval, CandleOutputInterval

router = APIRouter()

# Meta
@router.get(
        "/meta/exchanges", 
        response_model=list[MarketSchema.ExchangeRead], 
        summary="거래소 목록"
)
def list_exchanges(
    svcs: ServiceFactory = Depends(get_services),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return svcs.markets().list_exchanges(limit=limit, offset=offset)

@router.get(
        "/markets/instruments", 
        response_model=list[MarketSchema.MarketInstrumentItem], 
        summary="거래소 종목 목록"
)
def list_exchange_instruments(
    svcs: ServiceFactory = Depends(get_services),
    exchange_id: int | None = Query(None, ge=1),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    dtos = svcs.markets().list_exchange_instruments(exchange_id=exchange_id, limit=limit, offset=offset)
    return [MarketSchema.MarketInstrumentItem.model_validate(dto) for dto in dtos]

@router.get(
        "/markets/mapping", response_model=list[MarketSchema.MappingItem], summary="거래소-종목 매핑(선택)"
)
def list_mapping(
    svcs: ServiceFactory = Depends(get_services),
    exchange_id: int | None = Query(None, ge=1),
):
    return svcs.markets().list_mapping(exchange_id=exchange_id)

# Prices
@router.get(
        "/prices/candles", response_model=list[MarketSchema.CandleRead], summary="캔들 조회"
)
def list_candles(
    svcs: ServiceFactory = Depends(get_services),
    exchange_instrument_id: int = Query(..., ge=1),
    base: CandleBaseInterval | None = Query(None),
    output: CandleOutputInterval | None = Query(None),
    start: datetime | None = Query(None, description="UTC ISO8601"),
    end: datetime | None = Query(None, description="UTC ISO8601"),
    limit: int = Query(500, ge=1, le=2000),
    order: str = Query("asc", pattern="^(asc|desc)$"),
):
    return svcs.markets().list_candles(
        exchange_id=exchange_instrument_id,
        base=base,
        output=output,
        start=start,
        end=end,
        limit=limit,
        asc_order=(order == "asc"),
    )
