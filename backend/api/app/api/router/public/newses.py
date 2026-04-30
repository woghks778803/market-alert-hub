from datetime import datetime
from fastapi import Security, Response, APIRouter, Depends, Query, Path, Body, status
from app.core.constants import NewsPostsort
from app.service.sync.factory import ServiceFactory
from app.api.common.envelope import Envelope, ok, no_content
from app.api.deps import get_current_user, get_services, get_request_meta, RequestMeta
from app.api.schema import AuthSchema, NewsSchema
import app.api.openapi as OpenApi

router = APIRouter(prefix="/newses")

@router.get(
    "/posts",
    response_model=Envelope[list[NewsSchema.PostRead]],
    summary="뉴스 포스트 목록",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[list[NewsSchema.PostRead]],
            description="뉴스 포스트 목록 조회 성공",
        ),
        OpenApi.ERR_401,
        OpenApi.ERR_409,
    ),
)
def list_news_post(
    search: str | None = Query(None),
    cursor_at: datetime | None = Query(None, description="마지막 항목의 정렬 기준 시간 UTC ISO8601"),
    cursor_id: int | None = Query(None, description="마지막 항목의 news_item_id"),
    start: datetime | None = Query(None, description="UTC ISO8601"),
    end: datetime | None = Query(None, description="UTC ISO8601"),
    limit: int = Query(10, ge=1, le=20, description="조회 개수"),
    sort: NewsPostsort | None = Query(None, description="정렬"),
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.newses.list_news_post_by_filter(
        search=search,
        cursor_at=cursor_at,
        cursor_id=cursor_id,
        start=start,
        end=end,
        limit=limit,
        sort=sort,
    )
    return ok(rows, request_id=meta.request_id)