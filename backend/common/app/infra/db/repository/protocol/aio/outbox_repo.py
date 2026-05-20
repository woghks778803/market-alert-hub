from typing import Protocol
from app.domain import OutboxDTO

class OutboxRepo(Protocol):
    async def update_outbox_by_filter(
        self, filters: OutboxDTO.OutboxFilter, updates: OutboxDTO.OutboxUpdate
    ) -> int: ...
    async def list_outbox_by_filter(
        self,
        filters: OutboxDTO.OutboxFilter,
        *,
        limit: int | None = None,
        offset: int = 0,
        order_desc: bool = False,
        for_update: bool = False,
        skip_locked: bool = False,
    ) -> list[int]: ...  