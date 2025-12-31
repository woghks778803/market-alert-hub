from fastapi import APIRouter, Depends, Path, Query, Body

from app.core.constants import UserRole, UserStatus
from app.service.factory import ServiceFactory
from app.api.common.envelope import Envelope, ok, no_content
from app.api.deps import get_services, get_request_meta, RequestMeta
from app.api.schema import UserSchema
import app.api.openapi as OpenApi

router = APIRouter(
    prefix="/users",
)

@router.get(
    "", 
    response_model=Envelope[list[UserSchema.UserReadAdmin]], 
    summary="사용자 목록",
    responses=OpenApi.combine(
        OpenApi.OK(Envelope[list[UserSchema.UserReadAdmin]]),
    ),
)
def list_users(
    status: UserStatus | None = Query(None),
    role: UserRole | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.users.list_users_filter(status=status, role=role, limit=limit, offset=offset)
    return ok(rows, request_id=meta.request_id)

@router.get(
    "/{user_id}", 
    response_model=Envelope[UserSchema.UserReadAdmin], 
    summary="사용자 상세",
    responses=OpenApi.combine(
        OpenApi.OK(Envelope[UserSchema.UserReadAdmin]),
    ),
)
def get_user(
    user_id: int = Path(..., ge=1),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    result = svcs.users.get_user_admin_info(user_id=user_id)
    return ok(result, request_id=meta.request_id)

@router.patch(
    "/{user_id}", 
    response_model=Envelope[UserSchema.UserReadAdmin], 
    summary="사용자 속성 변경",
    responses=OpenApi.combine(
        OpenApi.OK(Envelope[UserSchema.UserReadAdmin]),
    ),
)
def update_user(
    user_id: int = Path(..., ge=1),
    payload: UserSchema.UserUpdateAdmin = Body(...),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    result = svcs.users.ensure_user(user_id=user_id, role=payload.role, status=payload.status)
    return ok(result, request_id=meta.request_id)

@router.delete(
    "/{user_id}", 
    summary="사용자 삭제(soft)",
    responses=OpenApi.combine(
        OpenApi.NO_CONTENT({}, description="완료")
    ),
)
def delete_user(
    user_id: int = Path(..., ge=1),
    svcs: ServiceFactory = Depends(get_services),
):
    svcs.users.delete_user(user_id=user_id)
    return no_content()
