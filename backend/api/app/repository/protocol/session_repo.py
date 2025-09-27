from typing import Protocol
from datetime import datetime
from app.infra.db.model import SessionModel

class SessionRepo(Protocol):

    def create(self, *, user_id: int, token_hash: str, expires_at: datetime,
               ip_addr: str | None, user_agent: str | None) -> SessionModel: ...

    def revoke(self, token_hash: str) -> int: ...

    def get_by_hash(self, token_hash: str) -> SessionModel | None : ...