from curses import meta
from datetime import datetime
from fastapi import Security, Response, APIRouter, Depends, Query, Path, Body, status
from app.core.constants import CandleBaseInterval, CandleOutputInterval, MarketSort
from app.service.factory import ServiceFactory
from app.api.common.envelope import Envelope, ok, no_content
from app.api.deps import get_current_user, get_services, get_request_meta, RequestMeta
from app.api.schema import AuthSchema, MarketSchema
import app.api.openapi as OpenApi

router = APIRouter(prefix="/markets")


@router.get(
    "/{exchange_instrument_id:int}",
    response_model=Envelope[MarketSchema.MarketRead],
    summary="마켓 심볼 상세 정보",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[list[MarketSchema.MarketRead]],  #  스키마도 래퍼로
            description="마켓 조회 성공",
        ),
        OpenApi.ERR_409,
    ),
)
def get_market(
    exchange_instrument_id: int = Path(..., ge=1),
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.markets.get_by_exchange_instrument_id(
        user_id=user.id,
        exchange_instrument_id=exchange_instrument_id,
    )
    return ok(rows, request_id=meta.request_id)


@router.get(
    "",
    response_model=Envelope[list[MarketSchema.MarketRead]],
    summary="마켓(거래소 종목) 목록",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[list[MarketSchema.MarketRead]],
            description="",
        ),
        OpenApi.ERR_409,
    ),
)
def list_markets(
    limit: int = Query(10, ge=1, le=20),
    offset: int = Query(0, ge=0),
    exchange_codes: list[str] | None = Query(None),
    search: str | None = Query(None),
    watchlist_only: bool = Query(False),
    sort: MarketSort = Query(None),
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.markets.list_by_filter(
        user_id=user.id,
        exchange_codes=exchange_codes,
        search=search,
        watchlist_only=watchlist_only,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return ok(rows, request_id=meta.request_id)


@router.get(
    "/exchanges",
    response_model=Envelope[list[MarketSchema.ExchangeRead]],
    summary="거래소 목록",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[list[MarketSchema.ExchangeRead]],  #  스키마도 래퍼로
            description="리스트 조회 성공",
        ),
        OpenApi.ERR_409,
    ),
)
def list_exchanges(
    limit: int = Query(10, ge=1, le=20),
    offset: int = Query(0, ge=0),
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.markets.list_exchange_by_filter(limit=limit, offset=offset)
    return ok(rows, request_id=meta.request_id)


@router.get(
    "/instruments",
    response_model=Envelope[list[MarketSchema.MarketInstrumentItem]],
    summary="종목 목록",
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
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.markets.list_exchange_instrument_by_filter(
        exchange_id=exchange_id, limit=limit, offset=offset
    )

    return ok(rows, request_id=meta.request_id)


@router.get(
    "/mappings",
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
def list_mappings(
    exchange_id: int | None = Query(None, ge=1),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.markets.list_mappings_exchange_id(exchange_id=exchange_id)
    return ok(rows, request_id=meta.request_id)


# Prices
@router.get(
    "/candles",
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
    output: CandleOutputInterval = Query(None),
    cursor: datetime | None = Query(None, description="UTC ISO8601"),
    start: datetime | None = Query(None, description="UTC ISO8601"),
    end: datetime | None = Query(None, description="UTC ISO8601"),
    limit: int = Query(500, ge=1, le=500),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.markets.list_candles_by_filter(
        exchange_instrument_id=exchange_instrument_id,
        output=output,
        cursor=cursor,
        start=start,
        end=end,
        limit=limit,
        asc_order=(order == "asc"),
    )
    return ok(rows, request_id=meta.request_id)


@router.get(
    "/stream/candles",
    response_model=Envelope[list[MarketSchema.CandleBase]],
    summary="실시간 캔들 조회",
    description="cursor > start, end 우선 (같이 값이 들어갈 경우 start, end는 무시됩니다)",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[list[MarketSchema.CandleBase]],
            description="리스트 조회 성공",
        ),
        OpenApi.ERR_409,
    ),
)
def stream_candles(
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    return ok({}, request_id=meta.request_id)


# @router.post(
#     "/candles/{base}",
#     status_code=status.HTTP_201_CREATED,
#     response_model=Envelope[MarketSchema.CandleIngestResult],
#     summary="캔들 스냅샷 저장",
#     description="내부 프로세스가 base 단위로 최신 캔들을 저장합니다. 항상 UPSERT로 동작합니다.",
#     responses=OpenApi.combine(
#         OpenApi.CREATED(
#             Envelope[MarketSchema.CandleIngestResult],
#             description="저장 성공",
#         ),
#     ),
# )
# def post_candles(
#     response: Response,
#     base: CandleBaseInterval = Path(..., description="기준 간격: 1m / 1h / 1d"),
#     payload: MarketSchema.CandleBase = Body(
#         ...,
#         example={
#             "exchange_instrument_id": 101,
#             "ts_open": "2025-03-15T12:34:00Z",
#             "open": 64123.12,
#             "high": 64200.0,
#             "low": 64010.5,
#             "close": 64180.7,
#             "volume": 12.3456,
#         },
#     ),
#     svcs: ServiceFactory = Depends(get_services),
#     meta: RequestMeta = Depends(get_request_meta),
# ):
#     item = MarketDTO.CandleBase(**payload.model_dump())
#     result = svcs.markets.ensure_snapshot(base=base, item=item)
#     return created(result, response=response, request_id=meta.request_id)
