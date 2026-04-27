from typing import Protocol, Sequence
from datetime import datetime
from app.core.constants import AlertStatus, AlertSort, AlertEventStatus, AlertDeliveryStatus
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

    def get_alert_snapshot_by_filter(
        self,
        *,
        alert_id: int,
        user_id: int | None = None,
        status: AlertStatus | None,
        archived_only: bool = False,
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

    def list_alert_event_by_status(
        self,
        *,
        status: AlertEventStatus | None,
        limit: int, 
        offset: int
    ) -> Sequence[AlertDTO.AlertEvent]: ...

    def list_alert_event_by_filter(
        self,
        *,
        alert_event_ids: Sequence[int],
        status: AlertEventStatus,
    ) -> Sequence[AlertDTO.AlertEvent]: ...

    def list_alert_delivery_by_filter(
        self,
        *,
        alert_event_ids: Sequence[int],
        status: AlertDeliveryStatus,
    ) -> Sequence[AlertDTO.AlertDelivery]: ...

    def list_alert_delivery_targets(
        self,
        *,
        alert_delivery_ids: Sequence[int],
    ) -> Sequence[AlertDTO.AlertDeliveryTarget]: ...

    def list_user_channel_by_filter(
        self,
        *,
        alert_event_ids: Sequence[int],
        status: AlertEventStatus,
    ) -> Sequence[AlertDTO.AlertEventChannel]: ...

    def list_alert_snapshot_by_status(
        self,
        *,
        status: AlertStatus | None,
        archived_only: bool = False,
        deleted_is_null: bool = True, 
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
    def add_alert_deliveries(
        self,
        alert_deliveries: Sequence[AlertDTO.AlertDeliveryCreate],
        *,
        chunk_size: int = 1000,
    ) -> int: ...

    
    def update_alert(
        self,
        row: AlertDTO.Alert,
        deleted_is_null: bool = True,
    ) -> None: ...

    def update_alert_status(self, alert_id: int, user_id: int, status: AlertStatus ) -> None: ...
    def update_alert_events_by_status(
        self,
        *,
        alert_event_ids: Sequence[int],
        from_status: AlertEventStatus,
        to_status: AlertEventStatus,
    ) -> None: ...
    def update_alert_deliveries_status(
        self,
        *,
        send_results: Sequence[AlertDTO.AlertDeliverySendResult],
        from_status: AlertDeliveryStatus,
        to_status: AlertDeliveryStatus,
        sent_at: datetime | None = None,
    ) -> int: ...

    def delete_alert(self, alert_id: int, user_id: int, deleted_at: datetime) -> None: ...