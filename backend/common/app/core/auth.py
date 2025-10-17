from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Dict, Any
from jose import jwt
from passlib.context import CryptContext
from app.runtime.settings import settings
import hashlib

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def token_hash(token: str) -> str: return hashlib.sha256(token.encode("utf-8")).hexdigest()
def hash_password(p: str) -> str: return _pwd.hash(p)
def verify_password(p: str, h: str) -> bool: return _pwd.verify(p, h)

def create_access_token(sub: Union[int, str], *, minutes: Optional[int] = None, claims: Optional[Dict[str, Any]] = None) -> str:
    m = minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    now = datetime.now(timezone.utc)
    payload = {"sub": str(sub), "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=m)).timestamp())}
    if claims: payload.update(claims)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
