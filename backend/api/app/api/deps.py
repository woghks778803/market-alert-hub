from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timezone

from app.core.constants import UserRole
from app.domain.shared.errors import AuthError, PermissionError
from app.runtime.bootstrap import get_core_services, get_core_api_config_bag
from app.service.factory import ServiceFactory
from dataclasses import dataclass

_bearer = HTTPBearer(auto_error=False)
api_config = get_core_api_config_bag()


@dataclass(frozen=True)
class RequestMeta:
    request_id: str
    timestamp: datetime


def get_request_meta(request: Request) -> RequestMeta:
    rid = getattr(request.state, "request_id", "-")
    return RequestMeta(request_id=rid, timestamp=datetime.now(timezone.utc))


def get_services(
    meta: RequestMeta = Depends(get_request_meta),
    svcs: ServiceFactory = Depends(get_core_services),
):

    svcs._trace_id = meta.request_id
    return svcs


def get_current_token(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """
    Authorization: Bearer <token> 헤더에서 토큰만 추출.
    라우터에서: token: str = Depends(get_current_token)
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
