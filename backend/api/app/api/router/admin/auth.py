from fastapi import APIRouter, Depends, Request, Body

from app.service.factory import ServiceFactory
from app.api.schema import auth as AuthSchema
from app.api.deps import get_services
import app.api.openapi as OpenApi



router = APIRouter(prefix="/auth")

@router.post(
    "/login",
    response_model=AuthSchema.TokenOut,
    summary="관리자 로그인 (JWT 발급)",
    responses=OpenApi.combine(
        OpenApi.OK(AuthSchema.TokenOut, description="로그인 성공"),
    ),
)
def admin_login(
    request: Request,
    payload: AuthSchema.Login = Body(
        ..., example={"email": "admin@example.com", "password": "P@ssw0rd!"}
    ),
    svcs: ServiceFactory = Depends(get_services),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    return svcs.auths().login(
        email=payload.email, password=payload.password, ip=ip, ua=ua, admin_chk=True
    )
