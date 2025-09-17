from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core import settings
from typing import Iterator


# --- DB session ---
engine = create_engine(settings.SQLALCHEMY_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FastAPI dependencies -----------------------------------------------------
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.domain import AuthError  # status=401, code="unauthorized"
from app.core.auth import decode_token  # 순수 유틸만 import
from app.service.user_service import UserService
from app.service.uow import UnitOfWork
from jose import JWTError, ExpiredSignatureError

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

def get_current_user(db=Depends(get_db), token: str = Depends(get_current_token)):
    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise AuthError("Token expired")
    except JWTError:
        raise AuthError("Invalid token")
    uid = int(payload["sub"])
    user = UserService(UnitOfWork(db)).get(uid)
    if not user:
        raise AuthError("User not found")
    return user

