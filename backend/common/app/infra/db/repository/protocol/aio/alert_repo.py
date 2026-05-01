from typing import Protocol, Sequence, Collection
from app.core.constants import AlertStatus
from app.domain import AlertDTO

class AlertRepo(Protocol):
    async def upsert_alert_events(
        self,
        events: Sequence[AlertDTO.AlertEventCreate],
        *,
        chunk_size: int = 1000,
    ) -> None: ...

    async def upsert_alerts_status(
        self,
        alert_ids: Collection[int],
        *,
        status: AlertStatus,
        chunk_size: int = 1000,
    ) -> None: ...