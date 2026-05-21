from fastapi import APIRouter, Depends, Request, Response, Body

from app.service.sync.factory import ServiceFactory
from app.api.schema import auth as AuthSchema
from app.api.common.envelope import Envelope, ok, created
from app.api.deps import (
    get_services, 
    get_request_meta, 
    get_current_user, 
    RequestMeta
)
import app.api.openapi as OpenApi



router = APIRouter(prefix="/auth")

@router.post(
    "/login",
    response_model=Envelope[AuthSchema.CurrentUser],
    summary="관리자 로그인",
    responses=OpenApi.combine(
        OpenApi.OK(Envelope[AuthSchema.CurrentUser], description="로그인 성공"),
    ),
)
def admin_login(
    request: Request,
    response: Response,
    payload: AuthSchema.Login = Body(
        ..., example={"email": "admin@example.com", "password": "P@ssw0rd!"}
    ),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    token_out = svcs.auths.login(
        email=payload.email, password=payload.password, ip=ip, ua=ua, admin_chk=True
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

    response.set_cookie(
        key="access_token",
        value=token_out.access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=svcs._config.access_token_minutes * 60,
        path="/",
    )
    
    user = get_current_user(
        svcs=svcs,
        token=token_out.access_token
    )

    return ok(user, request_id=meta.request_id)
