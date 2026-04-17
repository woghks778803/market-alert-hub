from typing import Callable, Sequence
from datetime import datetime
from app.core.constants import AlertStatus, AlertScope, AlertSort, ThrottleTimeframe, THROTTLE_SECONDS
from app.core.util.datetime import utcnow
from app.domain import AlertDTO, AlertRule, AlertPort
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import (
    NotFoundError,
    ConflictError
)

class AlertService:
    def __init__(
        self, 
        uow_factory: Callable[[], UnitOfWork],
        alert_snapshot: AlertPort.AlertSnapshot,
        alert_bucket: AlertPort.AlertBucket,
    ) -> None:
        self._uow_factory = uow_factory
        self._alert_snapshot = alert_snapshot
        self._alert_bucket = alert_bucket

    def get_alert_summary(
        self,
        *,
        user_id: int
    ):
        with self._uow_factory() as uow:
            result = uow.alerts.get_alert_summary(user_id=user_id)
            return result

    def get_by_user_alert(
        self,
        *,
        user_id: int,
        alert_id: int
    ):
        with self._uow_factory() as uow:
            alert = uow.alerts.get_alert_by_filter(
                user_id=user_id,
                alert_id=alert_id,
            )

            if alert is None:
                raise NotFoundError("Alert not found", target="alert")

            return alert

    def list_type_by_filter(self, *, search: str | None, limit: int, offset: int) -> Sequence[AlertDTO.AlertType]: 
        with self._uow_factory() as uow:
            rows = uow.alerts.list_type_by_filter(
                search=search, is_active=True, 
                limit=limit, offset=offset
            )
            return rows

    def list_alert_by_filter(
        self,
        *,
        user_id: int,
        sort: AlertSort | None,
        status: AlertStatus | None = None,
        archived_only: bool = False,
        limit: int,
        offset: int,
    ):
        with self._uow_factory() as uow:
            return uow.alerts.list_alert_by_filter(
                user_id=user_id,
                status=status,
                scope=AlertScope.SINGLE,
                archived_only=archived_only,
                sort=sort,
                limit=limit,
                offset=offset,
            )

    def create_alert(
        self,
        *,
        user_id: int,
        name: str,
        exchange_instrument_id: int | None,
        alert_type_id: int,
        is_once: bool,
        status: AlertStatus,
        scope: AlertScope,
        throttle_timeframe: ThrottleTimeframe,
        timezone: str,
        use_validity: bool,
        valid_from: datetime | None,
        valid_to: datetime | None,
        timeframe: str | None,
        period: int | None,
        params: dict,
    ):
        throttle_seconds = THROTTLE_SECONDS[throttle_timeframe]

        with self._uow_factory() as uow:

            alert_cnt = uow.alerts.get_alert_cnt(user_id=user_id)
            active_alert_cnt = uow.alerts.get_alert_cnt(user_id=user_id, status=AlertStatus.ACTIVE)

            # print(f"alert_cnt: {alert_cnt}, active_alert_cnt: {active_alert_cnt}")

            if status != AlertStatus.ACTIVE:
                raise ConflictError(
                    "Invalid alert status for create",
                    target="alert_status",
                )

            # TODO 현재는 고정 나중에 결제 서비스 넣을때 변경
            if alert_cnt >= AlertRule.MAX_NON_ARCHIVED_ALERTS_PER_USER:
                raise ConflictError(
                    "Alert limit already exceed", target="user_alert"
                )

            if active_alert_cnt >= AlertRule.MAX_ACTIVE_ALERTS_PER_USER:
                raise ConflictError(
                    "Alert limit already exceed", target="user_active_alert"
                )

            alert_type = uow.alerts.get_type_by_id(
                alert_type_id=alert_type_id,
                is_active=True,
            )

            if alert_type is None:
                raise NotFoundError("Alert type not found", target="alert_type")

            alert = uow.alerts.add_alert(
                AlertDTO.AlertCreate(
                    user_id=user_id,
                    alert_type_id=alert_type.id,
                    exchange_instrument_id=exchange_instrument_id,
                    name=name,
                    status=status,

                    # TODO: 추후 추가 개발시 고정값 해제
                    scope=AlertScope.SINGLE, 
                    timezone="UTC", 

                    timeframe=timeframe,
                    period=period,
                    params=params,

                    throttle_seconds=throttle_seconds,

                    valid_from=valid_from if use_validity else None,
                    valid_to=valid_to if use_validity else None,

                    is_once=is_once,
                )
            )

            uow.commit()

            alert_snapshot = uow.alerts.get_alert_snapshot_by_id(
                alert_id=alert.id,
                user_id=user_id,
            )

            self._sync_alert_snapshot(
                alert_id=alert.id,
                alert_snapshot=alert_snapshot,
            )

        return alert

    def change_alert(
        self,
        *,
        alert_id: int,
        user_id: int,
        name: str,
        exchange_instrument_id: int | None,
        alert_type_id: int,
        is_once: bool,
        status: AlertStatus,
        scope: AlertScope,
        throttle_timeframe: ThrottleTimeframe,
        timezone: str,
        use_validity: bool,
        valid_from: datetime | None,
        valid_to: datetime | None,
        timeframe: str | None,
        period: int | None,
        params: dict,
    ):
        now = utcnow()
        throttle_seconds = THROTTLE_SECONDS[throttle_timeframe]

        with self._uow_factory() as uow:
            alert = uow.alerts.get_by_id(
                alert_id=alert_id,
                user_id=user_id,
            )
            if alert is None:
                raise NotFoundError("Alert not found", target="alert")

            if alert.status == AlertStatus.ARCHIVED:
                raise ConflictError(
                    "Archived alert cannot be updated",
                    target="alert_status",
                )

            alert_type = uow.alerts.get_type_by_id(
                alert_type_id=alert_type_id,
                is_active=True,
            )

            if alert_type is None:
                raise NotFoundError("Alert type not found", target="alert_type")
            
            updated_alert = AlertDTO.Alert(
                id=alert_id,
                user_id=user_id,
                alert_type_id=alert_type.id,
                exchange_instrument_id=exchange_instrument_id,

                name=name,
                status=alert.status, # 수정 화면에 미제공

                scope=AlertScope.SINGLE,
                timezone="UTC",

                timeframe=timeframe,
                period=period,
                params=params,

                throttle_seconds=throttle_seconds,

                valid_from=valid_from if use_validity else None,
                valid_to=valid_to if use_validity else None,

                is_once=is_once,

                last_fired_at=alert.last_fired_at,
                updated_at=now,
            )

            uow.alerts.update_alert(
                updated_alert
            )

            uow.commit()

            alert_snapshot = uow.alerts.get_alert_snapshot_by_id(
                alert_id=alert_id,
                user_id=user_id,
            )

            self._sync_alert_snapshot(
                alert_id=alert_id,
                alert_snapshot=alert_snapshot,
            )

        return {"ok": True}

    def change_alert_status(
        self,
        user_id: int,
        alert_id: int,
        status: AlertStatus,
    ):
        now = utcnow()
        with self._uow_factory() as uow:
            alert = uow.alerts.get_by_id(
                alert_id=alert_id,
                user_id=user_id,
            )
            if alert is None:
                raise NotFoundError("Alert not found", target="alert")
            
            if alert.status == status:
                return {"ok": True}

            if alert.status == AlertStatus.ARCHIVED and status == AlertStatus.ACTIVE:
                raise ConflictError(
                    "Archived alert must be restored as paused",
                    target="alert_status",
                )

            # 일반 목록 -> 보관함 이동
            if status == AlertStatus.ARCHIVED:
                archived_alert_cnt = uow.alerts.get_alert_cnt(
                    user_id=user_id,
                    archived_only=True,
                )

                if archived_alert_cnt >= AlertRule.MAX_ARCHIVED_ALERTS_PER_USER:
                    raise ConflictError(
                        "Archived alert limit already exceed",
                        target="user_archived_alert",
                    )

            if alert.status == AlertStatus.ARCHIVED and status == AlertStatus.PAUSED:
                alert_cnt = uow.alerts.get_alert_cnt(
                    user_id=user_id,
                )

                if alert_cnt >= AlertRule.MAX_NON_ARCHIVED_ALERTS_PER_USER:
                    raise ConflictError(
                        "Alert limit already exceed",
                        target="user_alert",
                    )

            if status == AlertStatus.ACTIVE:
                active_alert_cnt = uow.alerts.get_alert_cnt(
                    user_id=user_id,
                    status=AlertStatus.ACTIVE,
                )

                if active_alert_cnt >= AlertRule.MAX_ACTIVE_ALERTS_PER_USER:
                    raise ConflictError(
                        "Alert limit already exceed",
                        target="user_active_alert",
                    )

            alert_type = uow.alerts.get_type_by_id(
                alert_type_id=alert.alert_type_id,
                is_active=True,
            )

            if alert_type is None:
                raise NotFoundError("Alert type not found", target="alert_type")

            uow.alerts.update_alert_status(
                alert_id=alert_id,
                user_id=user_id,
                status=status,
            )

            uow.commit()

            alert_snapshot = uow.alerts.get_alert_snapshot_by_id(
                alert_id=alert_id,
                user_id=user_id,
            )

            self._sync_alert_snapshot(
                alert_id=alert_id,
                alert_snapshot=alert_snapshot,
            )

        return {"ok": True}


    def delete_alert(
        self,
        user_id: int,
        alert_id: int,
    ):
        now = utcnow()
        with self._uow_factory() as uow:
            alert = uow.alerts.get_by_id(
                alert_id=alert_id,
                user_id=user_id,
            )
            if alert is None:
                raise NotFoundError("Alert not found", target="alert")

            uow.alerts.delete_alert(
                alert_id=alert_id,
                user_id=user_id,
                deleted_at=now
            )

            uow.commit()

            self._sync_alert_snapshot(
                alert_id=alert_id,
                alert_snapshot=None,
            )

        return {"ok": True}


    def sync_alerts(
        self,
        *,
        limit: int,
        offset: int,
    ):
        """
        Redis 알림 스냅샷 동기화 대상 조회
        """
        with self._uow_factory() as uow:
            alert_snapshots = uow.alerts.list_alert_snapshot_by_status(
                status=AlertStatus.ACTIVE,
                deleted_is_null=True,
                archived_only=False,
                asc_order=True,
                limit=limit,
                offset=offset,
            )
        
        result = []
        for alert_snapshot in alert_snapshots:
            payload = AlertRule.alert_snapshot_to_payload(alert_snapshot)

            bucket_key = self._alert_bucket.get_price_bucket_key(
                exchange_code=alert_snapshot.exchange_code,
                exchange_symbol=alert_snapshot.exchange_symbol,
            )
            payload["bucket_key"] = bucket_key

            result.append(payload)

        return result

    def _sync_alert_snapshot(
        self,
        *,
        alert_id: int,
        alert_snapshot: AlertDTO.AlertSnapshot | None,
    ) -> None:
        old_payload = self._alert_snapshot.alert_get(alert_id)
        if old_payload:
            old_exchange_code = old_payload.get("exchange_code")
            old_exchange_symbol = old_payload.get("exchange_symbol")
            
            if old_exchange_code and old_exchange_symbol:
                self._alert_bucket.alert_remove_price(
                    exchange_code=old_exchange_code,
                    exchange_symbol=old_exchange_symbol,
                    alert_id=alert_id,
                )

        if alert_snapshot is None:
            self._alert_snapshot.alert_remove(alert_id)
            return

        if alert_snapshot.status != AlertStatus.ACTIVE:
            self._alert_snapshot.alert_remove(alert_id)
            return

        payload = AlertRule.alert_snapshot_to_payload(alert_snapshot)

        bucket_key = self._alert_bucket.alert_add_price(
            exchange_code=alert_snapshot.exchange_code,
            exchange_symbol=alert_snapshot.exchange_symbol,
            alert_id=alert_snapshot.alert_id,
        )

        payload["bucket_key"] = bucket_key

        self._alert_snapshot.alert_upsert(
            alert_id=alert_snapshot.alert_id,
            payload=payload,
        )