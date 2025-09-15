# app/core/security.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext

from app.core.settings import settings  # .env 에서 불러오는 설정
# 전역 핸들링을 쓴다면 AuthError 사용, 아니면 주석 해제하지 말고 HTTPException을 쓰세요.
from app.core.errors import AuthError  # status=401, code="unauthorized"

# --- Password Hashing ---------------------------------------------------------
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """비밀번호를 bcrypt로 해싱."""
    return _pwd.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """평문/해시 일치 여부."""
    return _pwd.verify(plain_password, hashed_password)

# --- JWT ----------------------------------------------------------------------
_bearer = HTTPBearer(auto_error=False)

def create_access_token(
    subject: str,
    expires_minutes: Optional[int] = None,
    extra_claims: Optional[dict] = None,
) -> str:
    """
    액세스 토큰 생성.
    - subject: 보통 사용자 식별자 (email 또는 user_id)
    - expires_minutes: None이면 settings.ACCESS_TOKEN_EXPIRE_MINUTES 사용
    - extra_claims: 추가로 넣고 싶은 클레임(dict)
    """
    exp_minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=exp_minutes),
        **(extra_claims or {}),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def decode_token(token: str) -> dict:
    """JWT 디코드 (만료/무효 시 AuthError 발생 → 전역 핸들러로 처리)."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except ExpiredSignatureError:
        # 전역 에러 핸들러가 AppError를 표준 응답으로 변환
        raise AuthError(message="Token expired")
    except JWTError:
        raise AuthError(message="Invalid token")

# --- FastAPI dependencies -----------------------------------------------------
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
    payload = decode_token(token)
    sub = payload.get("sub")
    if not sub:
        raise AuthError(message="Invalid token payload")
    return sub
