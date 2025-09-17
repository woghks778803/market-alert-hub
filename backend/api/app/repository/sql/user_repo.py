from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.domain import ConflictError
from app.infra.db.model import User
from app.core.auth import hash_password, verify_password


class SqlUserRepo:
    """SQLAlchemy-backed implementation of UserRepo.

    Notes:
        - Each method commits explicitly for predictability.
        - Session lifecycle is owned by the caller (FastAPI dependency).
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, email: str, password: str) -> User:
        """Create a user with a hashed password."""
        user = User(email=email, hashed_password=hash_password(password))
        self._db.add(user)
        try:
            # ⬇️ INSERT를 강제 수행해 id를 배정 (persistent 상태가 됨)
            self._db.flush()            # commit은 UoW가
            
            # (옵션) DB default 컬럼까지 즉시 반영하고 싶으면 유지, 아니면 생략 가능
            self._db.refresh(user)
        except IntegrityError:
            raise ConflictError("USER_EXISTS", target="email")
        return user

    def get_by_email(self, email: str) -> Optional[User]:
        """Return a user by email, or None if not found."""
        return self._db.query(User).filter(User.email == email).first()
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return self._db.get(User, user_id)

    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Return user if email/password matches; otherwise None."""
        user = self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
