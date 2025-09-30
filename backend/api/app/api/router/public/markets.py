from datetime import datetime
from fastapi import APIRouter, Depends, Query, Path, Body, status
from app.core.constants import CandleBaseInterval, CandleOutputInterval
from app.service.factory import ServiceFactory
from app.api.deps import get_services
from app.api.schema import MarketSchema
import app.api.openapi as OpenApi

router = APIRouter()


# Meta
@router.get(
    "/meta/exchanges",
    response_model=list[MarketSchema.ExchangeRead],
    summary="거래소 목록",
)
def list_exchanges(
    svcs: ServiceFactory = Depends(get_services),
    limit: int = Query(10, ge=1, le=20),
    offset: int = Query(0, ge=0),
):
    dtos = svcs.markets().list_exchanges(limit=limit, offset=offset)
    return [MarketSchema.ExchangeRead.model_validate(dto) for dto in dtos]


@router.get(
    "/markets/instruments",
    response_model=list[MarketSchema.MarketInstrumentItem],
    summary="거래소 종목 목록",
)
def list_exchange_instruments(
    svcs: ServiceFactory = Depends(get_services),
    exchange_id: int | None = Query(None, ge=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    dtos = svcs.markets().list_exchange_instruments(
        exchange_id=exchange_id, limit=limit, offset=offset
    )
    return [MarketSchema.MarketInstrumentItem.model_validate(dto) for dto in dtos]


@router.get(
    "/markets/mapping",
    response_model=list[MarketSchema.MappingItem],
    summary="거래소-종목 매핑(선택)",
)
def list_mapping(
    svcs: ServiceFactory = Depends(get_services),
    exchange_id: int | None = Query(None, ge=1),
):
    return svcs.markets().list_mapping(exchange_id=exchange_id)


# Prices
@router.get(
    "/prices/candles", response_model=list[MarketSchema.CandleBase], summary="캔들 조회"
)
def list_candles(
    svcs: ServiceFactory = Depends(get_services),
    exchange_instrument_id: int = Query(..., ge=1),
    base: CandleBaseInterval | None = Query(None),
    output: CandleOutputInterval | None = Query(None),
    cursor: datetime | None = Query(None, description="UTC ISO8601"),
    start: datetime | None = Query(None, description="UTC ISO8601"),
    end: datetime | None = Query(None, description="UTC ISO8601"),
    limit: int = Query(500, ge=1, le=500),
    order: str = Query("asc", pattern="^(asc|desc)$"),
):
    return svcs.markets().list_candles(
        exchange_instrument_id=exchange_instrument_id,
        base=base,
        cursor=cursor,
        output=output,
        start=start,
        end=end,
        limit=limit,
        asc_order=(order == "asc"),
    )


@router.post(
    "/candles/{base}",
    status_code=status.HTTP_201_CREATED,
    response_model=MarketSchema.CandleIngestResult,
    summary="캔들 스냅샷 저장",
    description="내부 프로세스가 base 단위로 최신 캔들을 저장합니다. 항상 UPSERT로 동작합니다.",
    responses=OpenApi.combine(
        OpenApi.CREATED(
            MarketSchema.CandleIngestResult,
            description="저장 성공",
            example={"id": 12345, "created": True},
        ),
        OpenApi.ERR_400,
    ),
)
def post_candles(
    base: CandleBaseInterval = Path(..., description="기준 간격: 1m / 1h / 1d"),
    item: MarketSchema.CandleBase = Body(
        ...,
        example={
            "exchange_instrument_id": 101,
            "ts_open": "2025-03-15T12:34:00Z",
            "open": 64123.12,
            "high": 64200.0,
            "low": 64010.5,
            "close": 64180.7,
            "volume": 12.3456,
        },
    ),
    svcs: ServiceFactory = Depends(get_services),
):
    return svcs.markets().ingest_snapshot(base=base, item=item)
