from fastapi import Response, APIRouter, Depends, Query, Path, status

from app.service.factory import ServiceFactory
from app.api.common.envelope import Envelope, ok, created, no_content
from app.api.deps import get_services, get_current_user, get_request_meta, RequestMeta
from app.api.schema.watchlist import WatchlistCreate, WatchlistItemRead
from app.domain import AuthDTO
import app.api.openapi as OpenApi

router = APIRouter(prefix="/watchlists")


@router.get(
    "",
    response_model=Envelope[list[WatchlistItemRead]],
    summary="내 관심종목 목록",
    responses=OpenApi.combine(OpenApi.OK(Envelope[list[WatchlistItemRead]])),
)
def list_items(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    user: AuthDTO.AuthUser = Depends(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.watchlists.list_items_by_filter(
        user_id=user.id, limit=limit, offset=offset, is_asc=(order == "asc")
    )
    return ok(rows, request_id=meta.request_id)


@router.post(
    "",
    response_model=Envelope[WatchlistItemRead],
    summary="관심종목 등록",
    status_code=status.HTTP_201_CREATED,
    responses=OpenApi.combine(
        OpenApi.CREATED(Envelope[WatchlistItemRead]), OpenApi.ERR_409
    ),
)
def create_item(
    response: Response,
    payload: WatchlistCreate,
    user: AuthDTO.AuthUser = Depends(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    result = svcs.watchlists.create_item(
        user_id=user.id,
        exchange_instrument_id=payload.exchange_instrument_id,
        sort_order=payload.sort_order,
    )
    return created(
        WatchlistItemRead(
            id=result.id,
            exchange_instrument_id=result.exchange_instrument_id,
            sort_order=result.sort_order,
        ),
        response=response,
        request_id=meta.request_id,
        location=f"/watchlist/{result.id}",
    )


@router.delete(
    "/{exchange_instrument_id}",
    summary="관심종목 삭제",
    responses=OpenApi.combine(OpenApi.NO_CONTENT({}, description="완료")),
)
def delete_item(
    exchange_instrument_id: int = Path(..., ge=1),
    user: AuthDTO.AuthUser = Depends(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
):
    svcs.watchlists.delete_item(
        exchange_instrument_id=exchange_instrument_id, user_id=user.id
    )
    return no_content()
