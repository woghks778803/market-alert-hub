from jwt import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timezone
from functools import lru_cache
from dataclasses import dataclass
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core import dto as CoreDTO
from app.core.constants import UserRole

from app.domain.shared.errors import AuthError, PermissionError
from app.service.factory import ServiceFactory
from app.runtime.app_context import ApiContext
from app.runtime.bootstrap import (
    create_api_context,
)

_bearer = HTTPBearer(auto_error=False)
# api_config = get_core_api_config_bag()


@dataclass(frozen=True)
class RequestMeta:
    request_id: str
    timestamp: datetime


@dataclass(frozen=True)
class ApiRuntime:
    svcs: ServiceFactory
    config: CoreDTO.ApiConfigBag


@lru_cache(maxsize=1)
def get_app_context() -> ApiContext:
    return create_api_context()


def build_api_runtime() -> ApiRuntime:
    ctx = get_app_context()

    return ApiRuntime(
        svcs=ctx.svcs,
        config=ctx.config,
    )


def get_request_meta(request: Request) -> RequestMeta:
    rid = getattr(request.state, "request_id", "-")
    return RequestMeta(request_id=rid, timestamp=datetime.now(timezone.utc))


def get_services(
    ctx: ApiContext = Depends(get_app_context),
):
    return ctx.svcs


def get_current_token(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """
    Authorization: Bearer <token> 헤더에서 토큰만 추출.
    """
    if not creds or creds.scheme.lower() != "bearer":
        raise AuthError(message="Missing or invalid token")
    return creds.credentials


def get_current_user(
    svcs: ServiceFactory = Depends(get_services),
    token: str = Depends(get_current_token),
):
    try:
        payload = svcs.jwt.decode_token(token)
    except ExpiredSignatureError:
        raise AuthError("Token expired")
    except InvalidTokenError:
        raise AuthError("Invalid token")
    user_id = int(payload["sub"])
    if not user_id:
        raise AuthError(message="Invalid token payload")
    return svcs.auths.get_current_user(user_id, token)


def require_admin(user=Depends(get_current_user)):
    if getattr(user, "role", None) != UserRole.ADMIN:
        raise PermissionError("Admin role required", target="role")
