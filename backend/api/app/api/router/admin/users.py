from fastapi import APIRouter, Depends, Path, Query, Body

import app.api.openapi as OpenApi
from app.api.deps import get_services
from app.service.factory import ServiceFactory
from app.api.schema import UserSchema
from app.core.constants import UserRole, UserStatus

router = APIRouter(
    prefix="/users",
    responses=OpenApi.combine(OpenApi.ERR_401, OpenApi.ERR_500),
)

@router.get(
    "", 
    response_model=list[UserSchema.UserReadAdmin], 
    summary="사용자 목록",
    responses=OpenApi.combine(
        OpenApi.OK(list[UserSchema.UserReadAdmin]),
    ),
)
def list_users(
    svcs: ServiceFactory = Depends(get_services),
    status: UserStatus | None = Query(None),
    role: UserRole | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    rows = svcs.users().list(status=status, role=role, limit=limit, offset=offset)
    return [UserSchema.UserReadAdmin.model_validate(r) for r in rows]

@router.get(
    "/{user_id}", 
    response_model=UserSchema.UserReadAdmin, 
    summary="사용자 상세",
    responses=OpenApi.combine(
        OpenApi.OK(UserSchema.UserReadAdmin),
    ),
)
def get_user(
    user_id: int = Path(..., ge=1),
    svcs: ServiceFactory = Depends(get_services),
):
    user = svcs.users().get_by_id(user_id=user_id)
    return UserSchema.UserReadAdmin.model_validate(user)

@router.patch(
    "/{user_id}", 
    response_model=UserSchema.UserReadAdmin, 
    summary="사용자 속성 변경",
    responses=OpenApi.combine(
        OpenApi.OK(UserSchema.UserReadAdmin),
        OpenApi.ERR_400,      # ← 우리 포맷의 Validation Error
        OpenApi.ERR_403,
        OpenApi.ERR_404,
    ),
)
def update_user(
    user_id: int = Path(..., ge=1),
    payload: UserSchema.UserUpdateAdmin = Body(...),
    svcs: ServiceFactory = Depends(get_services),
):
    user = svcs.users().update(user_id=user_id, role=payload.role, status=payload.status)
    return UserSchema.UserReadAdmin.model_validate(user)

@router.delete("/{user_id}", status_code=204, summary="사용자 삭제(soft)")
def delete_user(
    user_id: int = Path(..., ge=1),
    svcs: ServiceFactory = Depends(get_services),
):
    svcs.users().delete(user_id=user_id)
    return
