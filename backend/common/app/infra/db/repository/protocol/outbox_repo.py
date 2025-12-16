from typing import Protocol, Sequence
from datetime import datetime
from app.domain import OutboxDTO
from app.infra.db.model import OutboxModel, OutboxAttemptModel

class OutboxRepo(Protocol):
    def add_outbox(self, row: OutboxModel) -> None: ...
    def add_outbox_attempt(self, row: OutboxAttemptModel) -> None: ...
    def get_by_outbox_id(self, id: int) -> OutboxModel | None: ...
    def update_outbox_by_filter(self, filters: OutboxDTO.OutboxFilter, updates: OutboxDTO.OutboxUpdate): ...
    def list_outboxs_by_filter(
        self, 
        filters: OutboxDTO.OutboxFilter,
        *,
        limit: int | None = None,
        offset: int = 0,
        order_desc: bool = False,
        for_update: bool = False,
        skip_locked: bool = False,
    ) -> list[int]: ...           # next_attempt_at IS NULL or <= now()

