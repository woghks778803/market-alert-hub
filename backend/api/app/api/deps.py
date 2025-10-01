from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as DbSession
from app.core.settings import settings
from typing import Iterator
from app.service.factory import ServiceFactory

# --- DB session ---
# engine = create_engine(
#     settings.SQLALCHEMY_URL,
#     future=True,
#     pool_pre_ping=True,   # 죽은 커넥션 사전 감지
#     pool_recycle=3600,    # MySQL 권장 (장기 유휴 커넥션 재생성)
#     # echo=True,          # 필요 시 디버깅
# )

# SessionLocal = sessionmaker(
#     bind=engine,
#     autoflush=False,
#     autocommit=False,
#     expire_on_commit=False,  # 커밋 이후도 객체 필드 접근 가능
#     future=True,
# )
engine = create_engine(settings.SQLALCHEMY_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

def get_db() -> Iterator[DbSession]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FastAPI dependencies -----------------------------------------------------
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.domain import AuthError, PermissionError
from app.service.uow import UnitOfWork
from app.core.auth import decode_token, token_hash
from app.core.constants import UserRole

from jose import JWTError, ExpiredSignatureError
from datetime import datetime, timezone

_bearer = HTTPBearer(auto_error=False)

def get_services(db: DbSession = Depends(get_db)) -> ServiceFactory:
    return ServiceFactory(lambda: UnitOfWork(db, owns_session=False))

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

def get_current_user_email(token: str = Depends(get_current_token)) -> str:
    """
    JWT의 sub를 email로 사용한다면 이 의존성으로 바로 주입 가능.
    라우터에서: email: str = Security(get_current_user_email)
    """
    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise AuthError(message="Token expired")
    except JWTError:
        raise AuthError(message="Invalid token")
    sub = payload.get("sub")
    if not sub:
        raise AuthError(message="Invalid token payload")
    return sub

def get_current_user_id(token: str = Depends(get_current_token)):
    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise AuthError("Token expired")
    except JWTError:
        raise AuthError("Invalid token")
    sub = int(payload["sub"])
    if not sub:
        raise AuthError(message="Invalid token payload")
    return sub

# --------------------------------------------


def get_current_user(
    svcs: ServiceFactory = Depends(get_services),
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
):
    token = get_current_token(creds)
    user_id = get_current_user_id(token)

    now = datetime.now(timezone.utc)
    with svcs.uow() as uow:  
        
        user = uow.users.get_by_id(user_id)
        if not user:
            raise AuthError("Invalid credentials", target="token")
        # 세션 유효성(선택이지만 권장)
        s = uow.sessions.get_by_hash(token_hash(token))  
        expires_at = s.expires_at
        revoked_at = s.revoked_at
        if expires_at is not None and expires_at.tzinfo is None: expires_at = expires_at.replace(tzinfo=timezone.utc)
        if revoked_at is not None and revoked_at.tzinfo is None: revoked_at = revoked_at.replace(tzinfo=timezone.utc)

        if not s or revoked_at or expires_at <= now:
            raise AuthError("Missing or invalid token", target="token")
        return user

def require_admin(user = Depends(get_current_user)):
    if getattr(user, "role", None) != UserRole.ADMIN:
        raise PermissionError("Admin role required", target="role")
    return user



# ---------------------------------------------------------
from dataclasses import dataclass

@dataclass(frozen=True)
class RequestMeta:
    request_id: str
    timestamp: datetime

def get_request_meta(request: Request) -> RequestMeta:
    rid = getattr(request.state, "request_id", "-")
    return RequestMeta(request_id=rid, timestamp=datetime.now(timezone.utc))