from __future__ import annotations

from sqlalchemy import select, desc, and_
from sqlalchemy.orm import Session as DbSession
from app.infra.db.model import UserModel
from ._utils import to_db_value
from ..protocol.user_repo import UserRepo

class SqlUserRepo(UserRepo):

    def __init__(self, db: DbSession) -> None:
        self._db = db

    def add(self, user: UserModel) -> UserModel:
        self._db.add(user); self._db.flush(); return user

    def get_by_email(self, email: str) -> UserModel | None:
        stmt = (
            select(UserModel).where(UserModel.email == email)
        )

        return self._db.execute(stmt).scalar_one_or_none()
    
    def get_by_id(self, user_id: int) -> UserModel | None:
        stmt = select(UserModel).where(and_(UserModel.is_deleted.is_(False), UserModel.id == user_id))
        return self._db.execute(stmt).scalar_one_or_none()
    
    def list(self, *, status: str | None, role: str | None, limit: int, offset: int) -> list[UserModel]:
        stmt = select(UserModel).where(UserModel.is_deleted.is_(False))
        if status:
            stmt = stmt.where(UserModel.status == to_db_value(status))
        if role:
            stmt = stmt.where(UserModel.role == to_db_value(role))

        stmt = stmt.order_by(desc(UserModel.created_at)).limit(limit).offset(offset)
        return self._db.execute(stmt).scalars().all()

