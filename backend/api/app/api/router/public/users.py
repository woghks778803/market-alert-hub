from fastapi import APIRouter, Depends, Security

from app.service.factory import ServiceFactory
from app.domain import AuthDTO
from app.api.schema import UserSchema
from app.api.common.envelope import Envelope, ok, created
from app.api.deps import (
    get_current_user,
    get_services,
    get_request_meta,
    RequestMeta,
)
import app.api.openapi as OpenApi

router = APIRouter(prefix="/user")


@router.get(
    "/me",
    response_model=Envelope[UserSchema.UserReadPublic],  #  래퍼 적용
    summary="내 프로필 조회",
    description="우상단 **Authorize**로 JWT 설정 후 호출하세요.",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[UserSchema.UserReadPublic],
            description="성공",
            example=OpenApi.wrap_example(
                {
                    "id": 5,
                    "email": "alice@example.com",
                    "nickname": "Alice",
                    "status": "active",
                }
            ),
        ),
    ),
)
def me(
    user: AuthDTO.AuthUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),  #
):
    u = svcs.users.get_user_public_info(user_id=user.id)
    return ok(UserSchema.UserReadPublic.model_validate(u), request_id=meta.request_id)
