from typing import Protocol, Sequence
from app.domain import AlertDTO

class AlertRepo(Protocol):
    async def upsert_alert_events(
        self,
        events: Sequence[AlertDTO.AlertEventCreate],
        *,
        chunk_size: int = 1000,
    ) -> int: ...