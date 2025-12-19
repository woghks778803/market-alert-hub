from typing import Protocol
from datetime import datetime
from app.infra.db.model import SessionModel

class SessionRepo(Protocol):

    def add_session(self, *, user_id: int, token_hash: bytes, expires_at: datetime,
               ip_addr: str | None, user_agent: str | None) -> SessionModel: ...

    def update_session(self, token_hash: bytes) -> int: ...

    def get_session_by_hash(self, token_hash: bytes) -> SessionModel | None : ...