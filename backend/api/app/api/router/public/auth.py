from fastapi import APIRouter, Depends, Body, Response, Request, status, Security

from app.service.factory import ServiceFactory
from app.domain import AuthDTO
from app.api.schema import UserSchema, AuthSchema
from app.api.common.envelope import Envelope, ok, created
from app.api.deps import (
    get_current_token,
    get_current_user,
    get_services,
    get_request_meta,
    RequestMeta,
)
import app.api.openapi as OpenApi

router = APIRouter(prefix="/auth")


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=Envelope[AuthSchema.SimpleOk],  # ✅ 래퍼 적용
    summary="유저 회원가입",
    description="이메일 중복 시 ConflictError로 처리(전역 핸들러에서 409로 매핑).",
    responses=OpenApi.combine(
        OpenApi.CREATED(
            Envelope[AuthSchema.SimpleOk],  # ✅ 스키마도 래퍼로
            description="회원가입 성공",
            example=OpenApi.wrap_example(
                {"ok": True}
            ),
        ),
        OpenApi.ERR_409,
    ),
)
def signup(
    response: Response,
    request: Request,
    payload: UserSchema.UserCreatePublic = Body(
        ...,
        example={
            "email": "alice@example.com",
            "nickname": "Alice",
            "password": "P@ssw0rd!",
        },
    ),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),  # ✅ request_id 주입
):
    token_out = svcs.auths.signup(
        email=payload.email,
        nickname=payload.nickname,
        password=payload.password,
    )

    return created(
        token_out, response=response, request_id=meta.request_id, location="/auth/me"
    )


@router.post(
    "/signin",
    response_model=Envelope[AuthSchema.TokenOut],  # ✅ 래퍼 적용
    summary="로그인 (JWT 발급)",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[AuthSchema.TokenOut],
            description="로그인 성공",
            example=OpenApi.wrap_example(
                {"user_id": 5, "access_token": "<jwt>", "token_type": "bearer"}
            ),
        ),
    ),
)
def signin(
    request: Request,
    payload: AuthSchema.Login = Body(
        ..., example={"email": "alice@example.com", "password": "P@ssw0rd!"}
    ),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),  # ✅
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    token_out = svcs.auths.signin(
        email=payload.email, password=payload.password, ip=ip, ua=ua, admin_chk=False
    )
    return ok(token_out, request_id=meta.request_id)


@router.post(
    "/logout",
    response_model=Envelope[AuthSchema.SimpleOk],  # ✅ 래퍼 적용
    summary="로그아웃 (세션 무효화)",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[AuthSchema.SimpleOk],
            description="로그아웃 성공",
            example=OpenApi.wrap_example({"ok": True}),
        ),
    ),
)
def logout(
    token: str = Depends(get_current_token),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),  # ✅
):
    svcs.auths.logout(token=token)
    return ok(AuthSchema.SimpleOk(ok=True), request_id=meta.request_id)


@router.get(
    "/me",
    response_model=Envelope[UserSchema.UserReadPublic],  # ✅ 래퍼 적용
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
    meta: RequestMeta = Depends(get_request_meta),  # ✅
):
    u = svcs.users.get_by_user_id(user_id=user.id)
    return ok(UserSchema.UserReadPublic.model_validate(u), request_id=meta.request_id)
