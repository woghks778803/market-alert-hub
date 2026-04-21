from typing import Protocol, Sequence
from datetime import datetime
from app.core.constants import AlertStatus, AlertSort
from app.domain import AlertDTO

class AlertRepo(Protocol):

    def get_alert_summary(
        self,
        *,
        user_id: int,
        deleted_is_null: bool = True,
    ) -> AlertDTO.AlertSummary: ...

    def get_alert_cnt(
        self, 
        *, 
        user_id: int, 
        status: AlertStatus | None = None,
        deleted_is_null: bool = True,
        archived_only: bool = False,
    ) -> int | None: ...

    def get_by_id(self, alert_id: int, user_id: int): ...

    def get_type_by_id(
        self,
        alert_type_id: int,
        is_active: bool, 
        deleted_is_null: bool = True,
    ) -> AlertDTO.AlertType | None: ...
    
    def get_alert_by_filter(
        self,
        *,
        user_id: int,
        alert_id: int,
        deleted_is_null: bool = True,
    ) -> AlertDTO.AlertSimple | None: ...

    def get_alert_snapshot_by_id(
        self,
        *,
        alert_id: int,
        user_id: int | None = None,
        deleted_is_null: bool = True,
    ) -> AlertDTO.AlertSnapshot | None: ...

    def list_type_by_filter(
        self, 
        *, 
        search: str | None, 
        is_active: bool, 
        deleted_is_null: bool = True, 
        asc_order: bool = False,
        limit: int, 
        offset: int
    ) -> Sequence[AlertDTO.AlertType]: ...

    def list_alert_snapshot_by_status(
        self,
        *,
        status: AlertStatus | None,
        deleted_is_null: bool = True, 
        archived_only: bool = False,
        asc_order: bool = False,
        limit: int, 
        offset: int
    ) -> Sequence[AlertDTO.AlertSnapshot]: ...

    def list_alert_by_filter(
        self,
        *,
        user_id: int,
        status: AlertStatus | None,
        sort: AlertSort,
        deleted_is_null: bool = True,
        archived_only: bool = False,
        limit: int,
        offset: int,
    ) -> Sequence[AlertDTO.AlertSimple]: ...
    
    def add_alert(self, row: AlertDTO.AlertCreate) -> AlertDTO.Alert: ...
    def update_alert(
        self,
        row: AlertDTO.Alert,
        deleted_is_null: bool = True,
    ) -> None: ...

    def update_alert_status(self, alert_id: int, user_id: int, status: AlertStatus ) -> None: ...
    def delete_alert(self, alert_id: int, user_id: int, deleted_at: datetime) -> None: ...