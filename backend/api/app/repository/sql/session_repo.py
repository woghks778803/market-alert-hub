from sqlalchemy import select
from app.infra.db.model.session import Session as SessionModel
from sqlalchemy.orm import Session as DbSession
from datetime import datetime
from typing import Optional
from ._utils import to_db_value

class SqlSessionRepo:
    def __init__(self, db: DbSession): self._db = db

    def create(self, *, user_id: int, token_hash: str, expires_at: datetime,
               ip_addr: str | None, user_agent: str | None) -> SessionModel:
        s = SessionModel(user_id=user_id, token_hash=token_hash,
                         expires_at=expires_at, ip_addr=ip_addr, user_agent=user_agent)
        self._db.add(s); self._db.flush(); return s

    def revoke(self, token_hash: str) -> int:
        s = self._db.execute(select(SessionModel).where(SessionModel.token_hash == token_hash)).scalar_one_or_none()
        if not s: return 0
        s.revoked_at = datetime.utcnow(); self._db.flush(); return 1

    def get_by_hash(self, token_hash: str) -> SessionModel | None:
        return self._db.execute(select(SessionModel).where(SessionModel.token_hash==token_hash)).scalar_one_or_none()