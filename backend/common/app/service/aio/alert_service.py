from typing import Callable, Sequence
from datetime import datetime
from app.core.util.datetime import utcnow
from app.domain import AlertDTO, AlertRule, AlertPort
from app.domain.shared.async_uow import AsyncUnitOfWork

class AlertService:
    def __init__(
        self, 
        uow_factory: Callable[[], AsyncUnitOfWork],
    ) -> None:
        self._uow_factory = uow_factory