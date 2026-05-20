from datetime import datetime
from fastapi import Security, Response, APIRouter, Depends, Query, Path, Body, status
from app.core.constants import NewsPostsort
from app.service.sync.factory import ServiceFactory
from app.api.common.envelope import Envelope, CursorPagination, ok, no_content
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
    cursor: str | None = Query(None),
    limit: int = Query(10, ge=1, le=20, description="조회 개수"),
    sort: NewsPostsort | None = Query(None, description="정렬"),
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    result = svcs.newses.list_news_post_by_filter(
        search=search,
        cursor=cursor,
        sort=sort,
        limit=limit,
    )

    return ok(
        data=result.items,
        request_id=meta.request_id,
        pagination=CursorPagination(
            limit=result.limit,
            has_next=result.has_next,
            next_cursor=result.next_cursor,
        ),
    )