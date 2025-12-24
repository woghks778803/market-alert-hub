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
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=Envelope[AuthSchema.SimpleOk],  # 래퍼 적용
    summary="유저 회원가입",
    description="이메일 중복 시 ConflictError로 처리(전역 핸들러에서 409로 매핑).",
    responses=OpenApi.combine(
        OpenApi.CREATED(
            Envelope[AuthSchema.SimpleOk],  #  스키마도 래퍼로
            description="회원가입 성공",
            example=OpenApi.wrap_example({"ok": True}),
        ),
        OpenApi.ERR_409,
    ),
)
def register(
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
    meta: RequestMeta = Depends(get_request_meta),  # request_id 주입
):
    token_out = svcs.auths.register(
        email=payload.email,
        nickname=payload.nickname,
        password=payload.password,
    )

    return created(
        token_out, response=response, request_id=meta.request_id, location="/auth/me"
    )


@router.post(
    "/login",
    response_model=Envelope[AuthSchema.TokenOut],  # 래퍼 적용
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
def login(
    request: Request,
    payload: AuthSchema.Login = Body(
        ..., example={"email": "alice@example.com", "password": "P@ssw0rd!"}
    ),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    token_out = svcs.auths.login(
        email=payload.email, password=payload.password, ip=ip, ua=ua, admin_chk=False
    )
    return ok(token_out, request_id=meta.request_id)


@router.post(
    "/resend-email-verification",
    response_model=Envelope[AuthSchema.SimpleOk],
    summary="이메일 인증 재발송",
    description="현재 로그인된 사용자 기준으로 이메일 인증 메일을 재발송합니다. (쿨다운/레이트리밋 정책 적용)",
    responses=OpenApi.combine(
        OpenApi.ERR_401,
        OpenApi.ERR_403,  # 예: 계정 비활성/차단 등 정책
        OpenApi.ERR_409,  # 예: 이미 인증됨
        OpenApi.ERR_429,  # 예: 쿨다운/레이트리밋
    ),
)
def resend_email_verification(
    request: Request,
    payload: AuthSchema.Login = Body(
        ..., example={"email": "alice@example.com", "password": "P@ssw0rd!"}
    ),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
) -> Envelope[AuthSchema.SimpleOk]:
    """
    - 액세스 토큰으로 유저 식별
    - 이메일 미검증 상태면 인증 메일 재발송(Outbox 생성)
    - 이미 인증된 경우 409 등으로 처리 가능
    """
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    svcs.auths.resend_email_verification(
        email=payload.email, password=payload.password, ip=ip, ua=ua
    )
    return ok(AuthSchema.SimpleOk(ok=True), request_id=meta.request_id)


@router.post(
    "/verify-email",
    response_model=Envelope[AuthSchema.SimpleOk],
    summary="이메일 인증",
    description="메일 링크로 전달된 토큰을 검증하여 이메일을 인증합니다.",
    # responses=OpenApi.ERR_400,  # TODO: 필요하면 에러 스펙 추가
)
def verify_email(
    request: Request,
    payload: AuthSchema.EmailVerifyToken = Body(
        ...,
        example={"token": "base64url-encoded-token"},
    ),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    svcs.auths.verify_email(token=payload.token, ip=ip, ua=ua)

    return ok(
        AuthSchema.SimpleOk(ok=True),
        request_id=meta.request_id,
    )


@router.post(
    "/change-email",
    response_model=Envelope[AuthSchema.SimpleOk],
    summary="이메일 변경",
    description="현재 비밀번호를 확인한 뒤 새 이메일로 인증 메일을 발송합니다.",
    responses=OpenApi.combine(
        OpenApi.ERR_400,
        OpenApi.ERR_401,
        OpenApi.ERR_409,  # 예: 이미 사용 중인 이메일 등
    ),
)
def change_email(
    payload: AuthSchema.ChangeEmailIn = Body(
        ...,
        example={
            "current_password": "P@ssw0rd!",
            "new_email": "new@example.com",
        },
    ),
    user: AuthDTO.AuthUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    """
    - 액세스 토큰으로 유저 식별
    - current_password 검증
    - 새 이메일로 인증 메일 발송 + 내부 상태 업데이트
    """

    svcs.auths.change_email(
        user_id=user.id,
        session_token=user.access_token,
        current_password=payload.current_password,
        new_email=payload.new_email,
    )

    return ok(AuthSchema.SimpleOk(ok=True), request_id=meta.request_id)


@router.post(
    "/logout",
    response_model=Envelope[AuthSchema.SimpleOk],  #  래퍼 적용
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
    meta: RequestMeta = Depends(get_request_meta),  #
):
    svcs.auths.logout(token=token)
    return ok(AuthSchema.SimpleOk(ok=True), request_id=meta.request_id)
