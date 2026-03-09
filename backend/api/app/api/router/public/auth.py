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
from fastapi.responses import RedirectResponse

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

router = APIRouter(prefix="/auth")


@router.post(
    "/reissue",
    status_code=status.HTTP_201_CREATED,
    response_model=Envelope[AuthSchema.TokenOut],  # 래퍼 적용
    summary="리프레시 토큰으로 액세스 토큰 갱신",
    description="리프레시 토큰을 사용하여 새로운 액세스 토큰을 발급합니다.",
    responses=OpenApi.combine(
        OpenApi.CREATED(
            Envelope[AuthSchema.TokenOut],  #  스키마도 래퍼로
            description="액세스 토큰 갱신 성공",
            example=OpenApi.wrap_example({"ok": True}),
        ),
        OpenApi.ERR_409,
    ),
)
def reissue_token(
    request: Request,
    response: Response,
    refresh_token: str = Cookie(..., alias="refresh_token"),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),  # request_id 주입
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    token_out = svcs.auths.reissue_token(refresh_token=refresh_token, ip=ip, ua=ua)

    # response.set_cookie(
    #     key="refresh_token",
    #     value=token_out.refresh_token,
    #     httponly=True,
    #     secure=False,
    #     samesite="lax",
    #     max_age=svcs._config.refresh_token_minutes * 60,
    #     path="/",
    # )

    return created(
        AuthSchema.TokenOut(
            access_token=token_out.access_token,
            token_type="bearer",
        ),
        response=response,
        request_id=meta.request_id,
        location="/",
    )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=Envelope[AuthSchema.TokenOut],
    summary="유저 회원가입",
    description="이메일 중복 시 ConflictError로 처리(전역 핸들러에서 409로 매핑).",
    responses=OpenApi.combine(
        OpenApi.CREATED(
            Envelope[AuthSchema.TokenOut],  #  스키마도 래퍼로
            description="회원가입 성공",
            example=OpenApi.wrap_example({"ok": True}),
        ),
        OpenApi.ERR_409,
    ),
)
def register(
    request: Request,
    response: Response,
    payload: UserSchema.UserCreateIn = Body(
        ...,
        example={
            "email": "alice@example.com",
            "nickname": "Alice",
            "password": "P@ssw0rd!",
            "agree_service": True,
            "agree_privacy": True,
            "agree_marketing": False,
        },
    ),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),  # request_id 주입
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    token_out = svcs.auths.register(
        email=payload.email,
        nickname=payload.nickname,
        password=payload.password,
        agree_service=payload.agree_service,
        agree_privacy=payload.agree_privacy,
        agree_marketing=payload.agree_marketing,
        ip=ip,
        ua=ua,
    )

    response.set_cookie(
        key="refresh_token",
        value=token_out.refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=svcs._config.refresh_token_minutes * 60,
        path="/",
    )

    return created(
        AuthSchema.TokenOut(
            access_token=token_out.access_token,
            token_type="bearer",
        ),
        response=response,
        request_id=meta.request_id,
        location="/auth/register",
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
    response: Response,
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

    response.set_cookie(
        key="refresh_token",
        value=token_out.refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=svcs._config.refresh_token_minutes * 60,
        path="/",
    )

    return ok(
        AuthSchema.TokenOut(
            access_token=token_out.access_token,
            token_type="bearer",
        ),
        request_id=meta.request_id,
    )


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
def send_email_verification(
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
) -> Envelope[AuthSchema.SimpleOk]:
    """
    - 이메일 미검증 상태면 인증 메일 재발송(Outbox 생성)
    - 이미 인증된 경우 409 등으로 처리 가능
    """
    svcs.auths.send_email_verification(
        user_id=user.id,
    )
    return ok(AuthSchema.SimpleOk(ok=True), request_id=meta.request_id)


@router.get(
    "/verify-email",
    response_model=Envelope[AuthSchema.SimpleOk],
    summary="이메일 인증",
    description="메일 링크로 전달된 토큰을 검증하여 이메일을 인증합니다.",
    # responses=OpenApi.ERR_400,  # TODO: 필요하면 에러 스펙 추가
)
def verify_email(
    request: Request,
    token: str = Query(..., description="verification token"),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    redirect_url = f"{svcs._config.public_web_base_url}/auth/verify-email-callback?"
    try:
        path = svcs.auths.verify_email(token=token)
    except Exception as e:
        path = "code=invalid_token"
    finally:
        return RedirectResponse(url=redirect_url + path, status_code=302)


@router.post(
    "/change-email",
    response_model=Envelope[AuthSchema.TokenOut],
    summary="이메일 변경",
    description="현재 비밀번호를 확인한 뒤 새 이메일로 인증 메일을 발송합니다.",
    responses=OpenApi.combine(
        OpenApi.ERR_401,
        OpenApi.ERR_409,  # 예: 이미 사용 중인 이메일 등
        OpenApi.ERR_429,
    ),
)
def change_email(
    payload: AuthSchema.ChangeEmailIn = Body(
        ...,
        example={
            "new_email": "new@example.com",
        },
    ),
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    """
    - 액세스 토큰으로 유저 식별
    - 새 이메일로 인증 메일 발송 + 내부 상태 업데이트
    """

    access_token = svcs.auths.change_email(
        user_id=user.id,
        # current_password=payload.current_password,
        new_email=payload.new_email,
    )

    return ok(
        AuthSchema.TokenOut(
            access_token=access_token,
            token_type="bearer",
        ),
        request_id=meta.request_id,
    )


@router.post(
    "/request-password-reset",
    response_model=Envelope[AuthSchema.SimpleOk],
    summary="비밀번호 재설정 요청",
    description="이메일을 입력하면 해당 이메일로 비밀번호 재설정 토큰이 발송됩니다. (쿨다운/레이트리밋 정책 적용)",
    responses=OpenApi.combine(
        OpenApi.ERR_429,
    ),
)
def send_password_reset(
    request: Request,
    payload: AuthSchema.PasswordForgot = Body(
        ..., example={"email": "alice@example.com"}
    ),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    token_out = svcs.auths.send_password_reset(email=payload.email)
    return ok(token_out, request_id=meta.request_id)


@router.post(
    "/change-password",
    response_model=Envelope[AuthSchema.SimpleOk],
    summary="비밀번호 재설정",
    description="비밀번호 재설정 토큰을 사용하여 비밀번호를 재설정합니다.",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[AuthSchema.SimpleOk],
            description="비밀번호 재설정 성공",
            example=OpenApi.wrap_example({"ok": True}),
        ),
        OpenApi.ERR_400,  # 예: 토큰 만료/무효, 비밀번호 정책 위반 등
        OpenApi.ERR_404,  # 예: 토큰 또는 사용자 미존재
    ),
)
def change_password(
    request: Request,
    payload: AuthSchema.ChangePasswordIn = Body(
        ...,
        example={
            "token": "base64url-encoded-token",
            "new_password": "N3wP@ss!",
        },
    ),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    result = svcs.auths.change_password(
        token=payload.token, new_password=payload.new_password
    )
    return ok(result, request_id=meta.request_id)


@router.post(
    "/verify-password-reset",
    response_model=Envelope[AuthSchema.SimpleOk],
    summary="비밀번호 재설정 토큰 검증",
    description="비밀번호 재설정 토큰이 유효한지 검증합니다.",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[AuthSchema.SimpleOk],
            description="비밀번호 재설정 토큰 검증 성공",
            example=OpenApi.wrap_example({"ok": True}),
        ),
        OpenApi.ERR_400,  # 예: 토큰 무효 등
        OpenApi.ERR_401,  # 예: 토큰 만료 등
    ),
)
def verify_password_reset(
    payload: AuthSchema.VerifyToken = Body(
        ...,
        example={
            "token": "base64url-encoded-token",
        },
    ),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    result = svcs.auths.verify_password_reset(token=payload.token)
    return ok(result, request_id=meta.request_id)


@router.post(
    "/logout",
    response_model=Envelope[AuthSchema.SimpleOk],
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
    response: Response,
    refresh_token: str = Cookie(..., alias="refresh_token"),
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),  #
):
    svcs.auths.logout(user_id=user.id, token=refresh_token)
    response.delete_cookie("refresh_token", path="/")
    return ok(AuthSchema.SimpleOk(ok=True), request_id=meta.request_id)


@router.get(
    "/oauth/start",
    response_model=Envelope[AuthSchema.SimpleOk],
    summary="OAuth 인가 요청 시작",
    responses=OpenApi.combine(
        OpenApi.ERR_400,
        OpenApi.ERR_401,
        OpenApi.ERR_404,
    ),
)
def oauth_start(
    # payload: AuthSchema.OAuthStartIn = Body(
    #     ...,
    #     example={
    #         "provider": "kakao",
    #         "agree_service": True,
    #         "agree_privacy": True,
    #         "agree_marketing": False,
    #     },
    # ),
    provider: str = Query(..., description="OAuth provider code (e.g., kakao)"),
    agree_service: bool = Query(
        ..., description="User consent to required service terms (true/false)"
    ),
    agree_privacy: bool = Query(
        ..., description="User consent to required privacy policy (true/false)"
    ),
    agree_marketing: bool = Query(
        ...,
        description="User consent to optional marketing communications (true/false)",
    ),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    try:

        oauth_result = svcs.auths.oauth_start(
            provider=provider,
            agree_marketing=agree_marketing,
            agree_privacy=agree_privacy,
            agree_service=agree_service,
        )

        # 실패 케이스 (urlencode 된 값)
        if oauth_result.authorize_path.startswith("source="):
            fail_url = (
                f"{svcs._config.public_web_base_url}/auth/oauth/fail?"
                f"{oauth_result.authorize_path}"
            )
            return RedirectResponse(url=fail_url, status_code=302)

        # 성공 케이스 (카카오 authorize path)
        authorize_url = (
            f"{svcs._config.kakao_auth_rest_base_url}" f"{oauth_result.authorize_path}"
        )

        return RedirectResponse(url=authorize_url, status_code=302)
    except Exception as e:
        error_url = (
            f"{svcs._config.public_web_base_url}/auth/oauth/fail"
            f"?code=internal_error"
        )
        return RedirectResponse(url=error_url, status_code=302)


@router.get(
    "/oauth/callback",
    response_model=Envelope[AuthSchema.SimpleOk],
    summary="OAuth 콜백 처리",
    responses=OpenApi.combine(
        OpenApi.ERR_400,
        OpenApi.ERR_401,
        OpenApi.ERR_404,
    ),
)
def oauth_callback(
    request: Request,
    code: str | None = Query(None, description="Authorization code"),
    state: str | None = Query(None, description="CSRF state"),
    error: str | None = Query(None, description="Error code"),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    try:
        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent")

        oauth_result = svcs.auths.oauth_callback(
            code=code,
            state=state,
            error=error,
            ip=ip,
            ua=ua,
        )

        path = oauth_result.authorize_path
        if path.startswith("source="):
            redirect_url = (
                f"{svcs._config.public_web_base_url}/auth/oauth/fail?" f"{path}"
            )
        else:
            redirect_url = f"{svcs._config.public_web_base_url}" f"{path}"

        redirect = RedirectResponse(url=redirect_url, status_code=302)

        redirect.set_cookie(
            key="refresh_token",
            value=oauth_result.refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=svcs._config.refresh_token_minutes * 60,
            path="/",
        )

        return redirect
    except Exception as e:
        error_url = (
            f"{svcs._config.public_web_base_url}/auth/oauth/fail"
            f"?code=internal_error"
        )
        return RedirectResponse(url=error_url, status_code=302)


@router.delete(
    "/deactivate",
    summary="회원 탈퇴 (soft delete + OAuth unlink)",
    responses=OpenApi.combine(OpenApi.NO_CONTENT({}, description="탈퇴 완료")),
)
def deactivate_user(
    response: Response,
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
):
    svcs.auths.deactivate_user(user_id=user.id)
    response.delete_cookie("refresh_token", path="/")
    return no_content()
