from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession
from app.infra.db.model import User as UserModel

from typing import Optional

class SqlUserRepo:

    def __init__(self, db: DbSession) -> None:
        self._db = db

    def add(self, user: UserModel) -> UserModel:
        self._db.add(user); self._db.flush(); return user

    def get_by_email(self, email: str) -> UserModel | None:
        return self._db.execute(select(UserModel).where(UserModel.email == email)).scalar_one_or_none()
    
    def get_by_id(self, user_id: int) -> Optional[UserModel]:
        return self._db.get(UserModel, user_id)

