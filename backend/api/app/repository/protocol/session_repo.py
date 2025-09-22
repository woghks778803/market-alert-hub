from typing import Protocol
from datetime import datetime
from app.infra.db.model import Session as SessionModel

class SessionRepo(Protocol):

    def create(self, *, user_id: int, token_hash: str, expires_at: datetime,
               ip_addr: str | None, user_agent: str | None) -> SessionModel: ...

    def revoke(self, token_hash: str) -> int: ...