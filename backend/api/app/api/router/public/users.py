from fastapi import (
    APIRouter,
    Depends,
    Security,
    Cookie,
    Response,
    Request,
    Body
)

from app.service.factory import ServiceFactory
from app.api.schema import UserSchema, AuthSchema
from app.api.common.envelope import Envelope, ok, created, no_content
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
def get_me(
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta), 
):
    u = svcs.users.get_user_public_info(user_id=user.id)
    return ok(UserSchema.UserReadPublic.model_validate(u), request_id=meta.request_id)


@router.patch(
    "/setting",
    response_model=Envelope[UserSchema.SimpleOk],
    summary="내 설정 수정",
    description=""
)
def change_user_setting(
    payload: UserSchema.UserSettingIn = Body(
        ...,
        example={
            "is_marketing": False,
            "is_quiet_hours": False,
        },
    ),
    user: AuthSchema.CurrentUser = Depends(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    result = svcs.users.change_user_settings(user.id, is_marketing=payload.is_marketing, is_quiet_hours=payload.is_quiet_hours)

    return ok(
        result, request_id=meta.request_id
    )