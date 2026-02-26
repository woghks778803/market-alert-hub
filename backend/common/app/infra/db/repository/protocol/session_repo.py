from typing import Protocol
from datetime import datetime
from app.domain import AuthDTO


class SessionRepo(Protocol):

    def add_session(
        self,
        *,
        user_id: int,
        token_hash: bytes,
        expires_at: datetime,
        ip_addr: str | None,
        user_agent: str | None
    ) -> AuthDTO.Session: ...

    def update_session(self, token_hash: bytes) -> int: ...

    def get_session_by_hash(
        self,
        token_hash: bytes,
        expires_after: datetime | None = None,
    ) -> AuthDTO.Session | None: ...
