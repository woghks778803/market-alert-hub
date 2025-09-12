from typing import Protocol, Optional
from sqlalchemy.orm import Session
from app.model.user import User
from app.core.security import hash_password, verify_password

class UserRepo(Protocol):
    def create(self, email: str, password: str) -> User: ...
    def get_by_email(self, email: str) -> Optional[User]: ...
    def authenticate(self, email: str, password: str) -> Optional[User]: ...

class SqlUserRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, email: str, password: str) -> User:
        user = User(email=email, hashed_password=hash_password(password))
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def authenticate(self, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
