from datetime import datetime
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_services
from app.service.factory import ServiceFactory
from app.api.schema.market import ExchangeRead, InstrumentRead, MappingItem, LatestPriceRead, Candle1mRead

router = APIRouter()

# Meta
@router.get(
        "/meta/exchanges", 
        response_model=list[ExchangeRead], 
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
        response_model=list[InstrumentRead], 
        summary="종목 목록"
)
def list_instruments(
    svcs: ServiceFactory = Depends(get_services),
    exchange_id: int | None = Query(None, ge=1),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    return svcs.markets().list_instruments(exchange_id=exchange_id, limit=limit, offset=offset)

@router.get(
        "/markets/mapping", response_model=list[MappingItem], summary="거래소-종목 매핑(선택)"
)
def list_mapping(
    svcs: ServiceFactory = Depends(get_services),
    exchange_id: int | None = Query(None, ge=1),
):
    return svcs.markets().list_mapping(exchange_id=exchange_id)

# Prices
@router.get(
        "/prices/latest", response_model=LatestPriceRead, summary="최신가 조회"
)
def get_latest(
    svcs: ServiceFactory = Depends(get_services),
    exchange_id: int = Query(..., ge=1),
    instrument_id: int = Query(..., ge=1),
):
    return svcs.markets().get_latest(exchange_id=exchange_id, instrument_id=instrument_id)

@router.get(
        "/prices/candles/1m", response_model=list[Candle1mRead], summary="1분 캔들 조회"
)
def list_candles_1m(
    svcs: ServiceFactory = Depends(get_services),
    exchange_id: int = Query(..., ge=1),
    instrument_id: int = Query(..., ge=1),
    start: datetime | None = Query(None, description="UTC ISO8601"),
    end: datetime | None = Query(None, description="UTC ISO8601"),
    limit: int = Query(500, ge=1, le=2000),
    order: str = Query("asc", pattern="^(asc|desc)$"),
):
    return svcs.markets().list_candles_1m(
        exchange_id=exchange_id,
        instrument_id=instrument_id,
        start=start,
        end=end,
        limit=limit,
        asc_order=(order == "asc"),
    )
