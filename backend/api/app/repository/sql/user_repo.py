from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session

from app.infra.db.model import User
from app.presentation.security import hash_password, verify_password


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
        self._db.commit()
        self._db.refresh(user)
        return user

    def get_by_email(self, email: str) -> Optional[User]:
        """Return a user by email, or None if not found."""
        return self._db.query(User).filter(User.email == email).first()

    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Return user if email/password matches; otherwise None."""
        user = self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
