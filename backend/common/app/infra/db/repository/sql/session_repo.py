from sqlalchemy import select
from app.core.util.datetime import utcnow
from app.infra.db.model import SessionModel
from sqlalchemy.orm import Session as DbSession
from datetime import datetime
from app.domain import AuthDTO
from ..protocol.session_repo import SessionRepo


class SqlSessionRepo(SessionRepo):
    def __init__(self, db: DbSession):
        self._db = db

    def add_session(
        self,
        *,
        user_id: int,
        token_hash: bytes,
        expires_at: datetime,
        ip_addr: str | None,
        user_agent: str | None
    ) -> AuthDTO.Session:
        s = SessionModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_addr=ip_addr,
            user_agent=user_agent,
        )
        self._db.add(s)
        self._db.flush()
        return s.to_dto()

    def update_session(self, token_hash: bytes) -> int:
        stmt = select(SessionModel).where(SessionModel.token_hash == token_hash)

        s = self._db.execute(stmt).scalar_one_or_none()
        if not s:
            return 0
        s.revoked_at = utcnow()
        self._db.flush()
        return 1

    def get_session_by_hash(
        self,
        token_hash: bytes,
        expires_after: datetime | None = None,
    ) -> AuthDTO.Session | None:
        stmt = select(SessionModel).where(SessionModel.token_hash == token_hash)

        if expires_after is not None:
            stmt = stmt.where(SessionModel.expires_at > expires_after)

        model = self._db.execute(stmt).scalar_one_or_none()
        return model.to_dto() if model else None
