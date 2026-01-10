from typing import Protocol
from app.domain import OutboxDTO
from app.infra.db.model import OutboxModel


class OutboxRepo(Protocol):
    def add_outbox(
        self, row: OutboxDTO.OutboxCreate, is_flush: bool
    ) -> OutboxDTO.Outbox: ...
    def add_outbox_attempt(
        self, row: OutboxDTO.OutboxAttemptCreate, is_flush: bool
    ) -> OutboxDTO.OutboxAttempt: ...
    def get_by_outbox_id(self, id: int) -> OutboxDTO.Outbox | None: ...
    def update_outbox_by_filter(
        self, filters: OutboxDTO.OutboxFilter, updates: OutboxDTO.OutboxUpdate
    ) -> int: ...
    def list_outboxs_by_filter(
        self,
        filters: OutboxDTO.OutboxFilter,
        *,
        limit: int | None = None,
        offset: int = 0,
        order_desc: bool = False,
        for_update: bool = False,
        skip_locked: bool = False,
    ) -> list[int]: ...  # next_attempt_at IS NULL or <= now()
