from typing import Protocol
from app.core.constants import AlertStatus, AlertSort
from app.domain import AlertDTO

class AlertRepo(Protocol):
    async def get_alert_summary(
        self,
        *,
        user_id: int,
        deleted_is_null: bool = True,
    ) -> AlertDTO.AlertSummary: ...