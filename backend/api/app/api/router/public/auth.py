from fastapi import APIRouter, Depends, Body, Request, status, Security

import app.api.openapi as OpenApi
from app.api.schema import UserSchema, AuthSchema
from app.api.deps import get_current_token, get_current_user_id, get_services

from app.service.factory import ServiceFactory
from app.core.auth import token_hash 

router = APIRouter(
    prefix="/auth",
    responses=OpenApi.combine(OpenApi.ERR_401, OpenApi.ERR_500),
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=AuthSchema.TokenOut,
    summary="유저 회원가입",
    description="이메일 중복 시 ConflictError로 처리(전역 핸들러에서 409로 매핑).",
    responses=OpenApi.combine(
        OpenApi.CREATED(AuthSchema.TokenOut, description="회원가입 성공",
                         example={"id": 1, "email": "alice@example.com"}),
        OpenApi.ERR_400, OpenApi.ERR_409,
    ),
)
def register(
    request: Request,
    payload: UserSchema.UserCreatePublic = Body(..., example={
        "email": "alice@example.com",
        "nickname": "Alice",
        "password": "P@ssw0rd!"
    }),
    svcs: ServiceFactory = Depends(get_services),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return svcs.auths().register(email=payload.email, nickname=payload.nickname, password=payload.password, ip=ip, ua=ua)


@router.post(
    "/login",
    response_model=AuthSchema.TokenOut,
    summary="로그인 (JWT 발급)",
    responses=OpenApi.combine(OpenApi.OK(AuthSchema.TokenOut, description="로그인 성공"), OpenApi.ERR_400),
)
def login(
    request: Request,
    payload: AuthSchema.Login = Body(..., example={"email": "alice@example.com", "password": "P@ssw0rd!"}),
    svcs: ServiceFactory = Depends(get_services),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return svcs.auths().login(email=payload.email, password=payload.password, ip=ip, ua=ua)


@router.post(
    "/logout",
    response_model=AuthSchema.SimpleOk,
    summary="로그아웃 (세션 무효화)",
    responses=OpenApi.combine(OpenApi.OK(AuthSchema.SimpleOk)),
)
def logout(
    token: str = Depends(get_current_token),            # ← 여기서 토큰만 주입
    svcs: ServiceFactory = Depends(get_services),
):
    return svcs.auths().logout(token_hash=token_hash(token))

@router.get(
    "/me",
    response_model=UserSchema.UserReadPublic,
    summary="내 프로필 조회",
    description="우상단 **Authorize**로 JWT 설정 후 호출하세요.",
    responses=OpenApi.combine(
        OpenApi.OK(UserSchema.UserReadPublic, description="성공",
           example={"access_token": "<jwt>", "token_type": "bearer"}),
        OpenApi.ERR_400, OpenApi.ERR_404
    ),
)
def me(
    user_id: str = Security(get_current_user_id),  # 🔒 Swagger에 보안 표시
    svcs: ServiceFactory = Depends(get_services),
):
    user = svcs.users().get_by_id(user_id=user_id)
    return UserSchema.UserReadPublic.model_validate(user)