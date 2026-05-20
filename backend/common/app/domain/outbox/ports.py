from typing import Protocol
from .dto import OutboxMessage

class AsyncOutboxEvent(Protocol):
    async def add_event(self, outbox_id: int) -> str:
        raise NotImplementedError


class OutboxEvent(Protocol):
    def claim_persist_outbox_events(
        self,
        *,
        consumer_name: str,
        min_idle_time_ms: int,
        count: int,
    ) -> list[OutboxMessage]:
        raise NotImplementedError

    def read_persist_outbox_events(
        self,
        *,
        consumer_name: str,
        count: int,
        block_ms: int,
    ) -> list[OutboxMessage]:
        raise NotImplementedError

    def ack_persist_outbox_events(
        self,
        *,
        message_ids: list[str],
    ) -> int:
        raise NotImplementedError

    def ensure_persist_group(self) -> None:
        raise NotImplementedError