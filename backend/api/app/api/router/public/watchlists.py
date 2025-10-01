from fastapi import APIRouter, Depends, Query, Path, status

from app.infra.db.model import UserModel
from app.service.factory import ServiceFactory
from app.api.common.envelope import Envelope, ok, created, no_content
from app.api.deps import get_services, get_current_user, get_request_meta, RequestMeta
from app.api.schema.watchlist import WatchlistCreate, WatchlistItemRead
import app.api.openapi as OpenApi

router = APIRouter(
    prefix="/watchlists"
)

@router.get(
    "",
    response_model=Envelope[list[WatchlistItemRead]],
    summary="내 관심종목 목록",
    responses=OpenApi.combine(
        OpenApi.OK(Envelope[list[WatchlistItemRead]])
    ),
)
def list_watchlist(
    svcs: ServiceFactory = Depends(get_services),
    user: UserModel = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.watchlists().list(user_id=user.id, limit=limit, offset=offset, is_asc=(order == "asc"))
    return ok(rows, request_id=meta.request_id)

@router.post(
    "",
    response_model=Envelope[WatchlistItemRead],
    summary="관심종목 등록",
    status_code=status.HTTP_201_CREATED,
    responses=OpenApi.combine(
        OpenApi.CREATED(Envelope[WatchlistItemRead]), 
        OpenApi.ERR_409
    ),
)
def create_watchlist(
    payload: WatchlistCreate,
    svcs: ServiceFactory = Depends(get_services),
    user: UserModel = Depends(get_current_user),
    meta: RequestMeta = Depends(get_request_meta),
):
    result = svcs.watchlists().create(user_id=user.id, data=payload)
    return created(result, request_id=meta.request_id)

@router.delete(
    "/{item_id}",
    summary="관심종목 삭제",
    responses=OpenApi.combine(
        OpenApi.NO_CONTENT({}, description="완료")
    ),
)
def delete_watchlist(
    item_id: int = Path(..., ge=1),
    svcs: ServiceFactory = Depends(get_services),
    user: UserModel = Depends(get_current_user),
):
    svcs.watchlists().delete(item_id=item_id, user_id=user.id)
    return no_content()
