from sqlalchemy import select
from app.core.util.datetime import utcnow
from app.infra.db.model import SessionModel
from sqlalchemy.orm import Session as DbSession
from datetime import datetime, timezone
from ..protocol.session_repo import SessionRepo

class SqlSessionRepo(SessionRepo):
    def __init__(self, db: DbSession): self._db = db

    def create_session(self, *, user_id: int, token_hash: bytes, expires_at: datetime,
               ip_addr: str | None, user_agent: str | None) -> SessionModel:
        s = SessionModel(user_id=user_id, token_hash=token_hash,
                         expires_at=expires_at, ip_addr=ip_addr, user_agent=user_agent)
        self._db.add(s); self._db.flush(); return s

    def update_session(self, token_hash: bytes) -> int:
        stmt = (
            select(SessionModel).where(SessionModel.token_hash==token_hash)
        )

        s = self._db.execute(stmt).scalar_one_or_none()
        if not s: return 0
        s.revoked_at = utcnow() 
        self._db.flush()
        return 1

    def get_session_by_hash(self, token_hash: bytes) -> SessionModel | None:
        stmt = (
            select(SessionModel).where(SessionModel.token_hash==token_hash)
        )
        
        return self._db.execute(stmt).scalar_one_or_none()