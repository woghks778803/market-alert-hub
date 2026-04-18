from uuid import uuid4
from fastapi import (
    APIRouter,
    Depends,
    Body,
    Response,
    Request,
    status,
    Security,
    Cookie,
    Query,
)
from app.core.constants import NoticeCategory, FAQCategory
from app.service.factory import ServiceFactory
from app.api.schema import SupportSchema, AuthSchema
from app.api.common.envelope import Envelope, ok, created, no_content
from app.api.deps import (
    get_optional_user,
    get_services,
    get_request_meta,
    RequestMeta,
)
import app.api.openapi as OpenApi

router = APIRouter(prefix="/supports")

@router.get(
    "/notices",
    response_model=Envelope[list[SupportSchema.NoticeRead]],
    summary="공지 목록 조회",
    responses=OpenApi.combine(
        OpenApi.OK(Envelope[list[SupportSchema.NoticeRead]]),
    ),
)
def list_notice(
    category: NoticeCategory | None = Query(None),
    limit: int = Query(10, ge=1, le=20),
    offset: int = Query(0, ge=0),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.supports.list_notice_by_filter(category=category, limit=limit, offset=offset)
    return ok(rows, request_id=meta.request_id,)


@router.get(
    "/notices/{id}",
    response_model=Envelope[SupportSchema.NoticeDetailRead],
    summary="공지 상세 조회",
    responses=OpenApi.combine(
        OpenApi.OK(Envelope[SupportSchema.NoticeDetailRead]),
        OpenApi.ERR_404,
    ),
)
def get_notice(
    request: Request,
    response: Response,
    id: int,
    user: AuthSchema.CurrentUser | None = Depends(get_optional_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    cookie_id = request.cookies.get("vid")
    
    if not cookie_id:
        cookie_id = str(uuid4())
        response.set_cookie("vid", cookie_id, max_age=60*60*24*365)

    row = svcs.supports.get_notice_by_id(id, user_id=user.id if user else None, client_ip=ip, cookie_id=cookie_id)
    return ok(row, request_id=meta.request_id,)


@router.get(
    "/faqs",
    response_model=Envelope[list[SupportSchema.FAQRead]],
    summary="FAQ 목록 조회",
    responses=OpenApi.combine(
        OpenApi.OK(Envelope[list[SupportSchema.FAQRead]]),
    ),
)
def list_faq(
    search: str | None = Query(None),
    category: FAQCategory | None = Query(None),
    limit: int = Query(10, ge=1, le=20),
    offset: int = Query(0, ge=0),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.supports.list_faq_by_filter(search=search, category=category, limit=limit, offset=offset)
    return ok(rows, request_id=meta.request_id,)
