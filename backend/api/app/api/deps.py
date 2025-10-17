# --- FastAPI dependencies -----------------------------------------------------
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session as DbSession
from typing import Iterator
from app.service.factory import ServiceFactory

from app.domain import AuthError, PermissionError
from app.infra.db.uow import UnitOfWork
from app.infra.db.engine import SessionLocal
from app.core.auth import decode_token, token_hash
from app.core.constants import UserRole

from jose import JWTError, ExpiredSignatureError
from datetime import datetime, timezone
from app.runtime.bootstrap import create_service_factory


def get_services() -> ServiceFactory:
    uow_provider = lambda: UnitOfWork(SessionLocal, owns_session=True)
    return create_service_factory(uow_provider)


_bearer = HTTPBearer(auto_error=False)

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
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise AuthError("Token expired")
    except JWTError:
        raise AuthError("Invalid token")
    user_id = int(payload["sub"])
    if not user_id:
        raise AuthError(message="Invalid token payload")

    return svcs.auths.get_current_user(user_id, token)


def require_admin(user=Depends(get_current_user)):
    if getattr(user, "role", None) != UserRole.ADMIN:
        raise PermissionError("Admin role required", target="role")


# ---------------------------------------------------------
from dataclasses import dataclass


@dataclass(frozen=True)
class RequestMeta:
    request_id: str
    timestamp: datetime


def get_request_meta(request: Request) -> RequestMeta:
    rid = getattr(request.state, "request_id", "-")
    return RequestMeta(request_id=rid, timestamp=datetime.now(timezone.utc))
