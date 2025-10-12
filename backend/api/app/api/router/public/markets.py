from datetime import datetime
from fastapi import APIRouter, Depends, Query, Path, Body, status
from app.core.constants import CandleBaseInterval, CandleOutputInterval
from app.service.factory import ServiceFactory
from app.api.common.envelope import Envelope, ok, created
from app.api.deps import get_services, get_request_meta, RequestMeta
from app.api.schema import MarketSchema
import app.api.openapi as OpenApi

router = APIRouter()


# Meta
@router.get(
    "/meta/exchanges",
    response_model=Envelope[list[MarketSchema.ExchangeRead]],
    summary="거래소 목록",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[list[MarketSchema.ExchangeRead]],  # ✅ 스키마도 래퍼로
            description="리스트 조회 성공",
        ),
        OpenApi.ERR_409,
    ),
)
def list_exchanges(
    limit: int = Query(10, ge=1, le=20),
    offset: int = Query(0, ge=0),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.markets.list_exchanges(limit=limit, offset=offset)
    return ok(rows, request_id=meta.request_id)


@router.get(
    "/markets/instruments",
    response_model=Envelope[list[MarketSchema.MarketInstrumentItem]],
    summary="거래소 종목 목록",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[list[MarketSchema.MarketInstrumentItem]], 
            description="리스트 조회 성공",
        ),
        OpenApi.ERR_409,
    ),
)
def list_exchange_instruments(
    exchange_id: int | None = Query(None, ge=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.markets.list_exchange_instruments(
        exchange_id=exchange_id, limit=limit, offset=offset
    )

    return ok(rows, request_id=meta.request_id)


@router.get(
    "/markets/mapping",
    response_model=Envelope[list[MarketSchema.MappingItem]],
    summary="거래소-종목 매핑(선택)",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[list[MarketSchema.MappingItem]], 
            description="리스트 조회 성공",
        ),
        OpenApi.ERR_409,
    ),
)
def list_mapping(
    exchange_id: int | None = Query(None, ge=1),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.markets.list_mapping(exchange_id=exchange_id)
    return ok(rows, request_id=meta.request_id)


# Prices
@router.get(
    "/prices/candles", 
    response_model=Envelope[list[MarketSchema.CandleBase]], 
    summary="캔들 조회",
    description="cursor > start, end 우선 (같이 값이 들어갈 경우 start, end는 무시됩니다)",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[list[MarketSchema.CandleBase]], 
            description="리스트 조회 성공",
        ),
        OpenApi.ERR_409,
    ),
)
def list_candles(
    exchange_instrument_id: int = Query(..., ge=1),
    output: CandleOutputInterval | None = Query(None),
    cursor: datetime | None = Query(None, description="UTC ISO8601"),
    start: datetime | None = Query(None, description="UTC ISO8601"),
    end: datetime | None = Query(None, description="UTC ISO8601"),
    limit: int = Query(500, ge=1, le=500),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.markets.list_candles(
        exchange_instrument_id=exchange_instrument_id,
        output=output,
        cursor=cursor,
        start=start,
        end=end,
        limit=limit,
        asc_order=(order == "asc"),
    )
    return ok(rows, request_id=meta.request_id)


@router.post(
    "/candles/{base}",
    status_code=status.HTTP_201_CREATED,
    response_model=Envelope[MarketSchema.CandleIngestResult],
    summary="캔들 스냅샷 저장",
    description="내부 프로세스가 base 단위로 최신 캔들을 저장합니다. 항상 UPSERT로 동작합니다.",
    responses=OpenApi.combine(
        OpenApi.CREATED(
            Envelope[MarketSchema.CandleIngestResult],
            description="저장 성공",
        ),
    ),
)
def post_candles(
    base: CandleBaseInterval = Path(..., description="기준 간격: 1m / 1h / 1d"),
    payload: MarketSchema.CandleBase = Body(
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
    meta: RequestMeta = Depends(get_request_meta),
):
    result = svcs.markets.ingest_snapshot(base=base, item=payload)
    return created(result, request_id=meta.request_id)
