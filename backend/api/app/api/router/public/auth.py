from fastapi import APIRouter, Depends, Body, Request, status, Security

from app.core.auth import token_hash
from app.infra.db.model import UserModel
from app.service.factory import ServiceFactory
from app.api.schema import UserSchema, AuthSchema
from app.api.common.envelope import Envelope, ok, created
from app.api.deps import get_current_token, get_current_user, get_services, get_request_meta, RequestMeta
import app.api.openapi as OpenApi

router = APIRouter(prefix="/auth")

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=Envelope[AuthSchema.TokenOut],  # ✅ 래퍼 적용
    summary="유저 회원가입",
    description="이메일 중복 시 ConflictError로 처리(전역 핸들러에서 409로 매핑).",
    responses=OpenApi.combine(
        OpenApi.CREATED(
            Envelope[AuthSchema.TokenOut],  # ✅ 스키마도 래퍼로
            description="회원가입 성공",
            example=OpenApi.wrap_example({   # ✅ 예시를 래퍼로 감쌈
                "user_id": 5,
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiaWF0IjoxNzU5MTM0NjM2LCJleHAiOjE3NTkxMzgyMzZ9.pa5udqz-ZTYAQ7GIznr0FmB9zdrRNmJBpDjecPii0X8",
                "token_type": "bearer"
            }),
        ),
        OpenApi.ERR_400,
        OpenApi.ERR_409,
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
    meta: RequestMeta = Depends(get_request_meta),  # ✅ request_id 주입
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    token_out = svcs.auths().register(email=payload.email, nickname=payload.nickname, password=payload.password, ip=ip, ua=ua)
    # ✅ 공통 ok/created 사용
    body, status_code, headers = created(token_out, request_id=meta.request_id, location="/auth/me")
    return body, status_code, headers

@router.post(
    "/login",
    response_model=Envelope[AuthSchema.TokenOut],  # ✅ 래퍼 적용
    summary="로그인 (JWT 발급)",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[AuthSchema.TokenOut],
            description="로그인 성공",
            example=OpenApi.wrap_example({
                "user_id": 5,
                "access_token": "<jwt>",
                "token_type": "bearer"
            }),
        ),
        OpenApi.ERR_400
    ),
)
def login(
    request: Request,
    payload: AuthSchema.Login = Body(..., example={"email": "alice@example.com", "password": "P@ssw0rd!"}),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),  # ✅
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    token_out = svcs.auths().login(email=payload.email, password=payload.password, ip=ip, ua=ua, admin_chk=False)
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
    svcs.auths().logout(token_hash=token_hash(token))
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
            example=OpenApi.wrap_example({
                "id": 5,
                "email": "alice@example.com",
                "nickname": "Alice",
                "status": "active"
            }),
        ),
        OpenApi.ERR_400, OpenApi.ERR_404
    ),
)
def me(
    user: UserModel = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),  # ✅
):
    u = svcs.users().get_by_id(user_id=user.id)
    return ok(UserSchema.UserReadPublic.model_validate(u), request_id=meta.request_id)

