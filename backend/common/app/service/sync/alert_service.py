from typing import Callable, Sequence
from datetime import datetime
from app.core.constants import (
    AlertDeliveryStatus, 
    AlertEventStatus, 
    AlertStatus, 
    AlertSort, 
    ThrottleTimeframe, 
    THROTTLE_SECONDS
)
from app.core.util.datetime import utcnow
from app.domain import AlertDTO, AlertRule, AlertPort, ChannelDTO, ChannelPort
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import (
    NotFoundError,
    ConflictError
)

class AlertService:
    def __init__(
        self, 
        uow_factory: Callable[[], UnitOfWork],
        channel_message_providers: dict[str, ChannelPort.ChannelMessage],
        alert_snapshot: AlertPort.AlertSnapshot,
        alert_bucket: AlertPort.AlertBucket,
    ) -> None:
        self._uow_factory = uow_factory
        self._channel_message_providers = channel_message_providers
        self._alert_snapshot = alert_snapshot
        self._alert_bucket = alert_bucket
        self._alert_message_builder = AlertRule.AlertMessageBuilder()

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

    def list_alert_type_by_filter(self, *, search: str | None, limit: int, offset: int) -> Sequence[AlertDTO.AlertType]: 
        with self._uow_factory() as uow:
            rows = uow.alerts.list_alert_type_by_filter(
                search=search, is_active=True, asc_order=True,
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
        cursor: str | None
    ) -> AlertDTO.AlertListResult:

        sort = sort or AlertSort.RECENT_UPDATED

        decode_cursor = None
        if cursor:
            decode_cursor = AlertRule.decode_alert_cursor(cursor)

            if decode_cursor.sort != sort:
                decode_cursor = None


        with self._uow_factory() as uow:
            rows = uow.alerts.list_alert_by_filter(
                user_id=user_id,
                status=status,
                archived_only=archived_only,
                cursor=decode_cursor,
                limit=limit+1,
                sort=sort,
            )
        
        has_next = len(rows) > limit
        items = list(rows[:limit])

        next_cursor = None
        if has_next and items:
            next_cursor = AlertRule.make_alert_cursor(
                sort=sort,
                item=items[-1],
            )

        return AlertDTO.AlertListResult(
            items=items,
            limit=limit,
            has_next=has_next,
            next_cursor=next_cursor,
        )

    def list_alert_log_by_filter(
        self,
        *,
        user_id: int,
        status: AlertEventStatus | None = None,
        limit: int,
        cursor: str | None
    ) -> AlertDTO.AlertLogListResult:

        decode_cursor = None
        if cursor:
            decode_cursor = AlertRule.decode_alert_log_cursor(cursor)


        with self._uow_factory() as uow:
            rows = uow.alerts.list_alert_event_by_filter(
                user_id=user_id,
                status=status,
                cursor=decode_cursor,
                limit=limit+1,
            )

        logs: list[AlertDTO.AlertLog] = []
        for row in rows:
            content = self._alert_message_builder.build(
                context=row.context or {},
                trigger_value=row.trigger_value,
                alert_event_id=row.id,
            )

            log = AlertRule.make_alert_log(
                event=row,
                content=content,
            )

            logs.append(log)

        has_next = len(logs) > limit
        items = list(logs[:limit])

        next_cursor = None
        if has_next and items:
            next_cursor = AlertRule.make_alert_log_cursor(
                item=items[-1],
            )

        return AlertDTO.AlertLogListResult(
            items=items,
            limit=limit,
            has_next=has_next,
            next_cursor=next_cursor,
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
        throttle_timeframe: ThrottleTimeframe,
        timezone: str,
        use_validity: bool,
        valid_from: datetime | None,
        valid_to: datetime | None,
        # timeframe: str | None,
        # period: int | None,
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
                    timezone="UTC", 

                    params=params,

                    throttle_seconds=throttle_seconds,
                    is_once=is_once,

                    valid_from=valid_from if use_validity else None,
                    valid_to=valid_to if use_validity else None,
                )
            )

            uow.commit()

            alert_snapshot = uow.alerts.get_alert_snapshot_by_filter(
                alert_id=alert.id,
                user_id=user_id,
                status=AlertStatus.ACTIVE,
                archived_only=False,
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
        throttle_timeframe: ThrottleTimeframe,
        timezone: str,
        use_validity: bool,
        valid_from: datetime | None,
        valid_to: datetime | None,
        # timeframe: str | None,
        # period: int | None,
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

                timezone="UTC",

                # timeframe=timeframe,
                # period=period,
                params=params,

                throttle_seconds=throttle_seconds,

                valid_from=valid_from if use_validity else None,
                valid_to=valid_to if use_validity else None,

                is_once=is_once,

                last_fired_at=alert.last_fired_at,
                created_at=alert.created_at,
                updated_at=now,
                deleted_at=alert.deleted_at,
            )

            uow.alerts.update_alert(
                updated_alert
            )

            uow.commit()

            alert_snapshot = uow.alerts.get_alert_snapshot_by_filter(
                alert_id=alert_id,
                user_id=user_id,
                status=AlertStatus.ACTIVE,
                archived_only=False,
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

            alert_snapshot = uow.alerts.get_alert_snapshot_by_filter(
                alert_id=alert_id,
                user_id=user_id,
                status=AlertStatus.ACTIVE,
                archived_only=False,
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


    def dispatch_alert_events(
        self,
        batch_size: int,
    ):
        started_at = utcnow()

        selected_count = 0
        queued_count = 0
        delivery_count = 0
        sent_count = 0
        failed_count = 0
        skipped_count = 0

        with self._uow_factory() as uow:
            # 1. PENDING alert_events 조회
            alert_events = uow.alerts.list_alert_event_by_status(
                status=AlertEventStatus.PENDING,
                limit=batch_size,
                offset=0,
            )

            if not alert_events:
                return {
                    "selected_count": 0,
                    "queued_count": 0,
                    "delivery_count": 0,
                    "sent_count": 0,
                    "failed_count": 0,
                    "skipped_count": 0,
                }

            selected_count = len(alert_events)
            alert_event_ids = [event.id for event in alert_events]

            # 2. alert_events QUEUED 선점
            uow.alerts.update_alert_events_by_status(
                alert_event_ids=alert_event_ids,
                from_status=AlertEventStatus.PENDING,
                to_status=AlertEventStatus.QUEUED,
            )

            # 3. 선점한 alert_events 재조회
            queued_events = uow.alerts.list_alert_event_from_ids(
                alert_event_ids=alert_event_ids,
                status=AlertEventStatus.QUEUED,
            )

            if not queued_events:
                uow.commit()
                return {
                    "selected_count": selected_count,
                    "queued_count": 0,
                    "delivery_count": 0,
                    "sent_count": 0,
                    "failed_count": 0,
                    "skipped_count": 0,
                }

            queued_count = len(queued_events)
            queued_event_ids = [event.id for event in queued_events]
            # print("queued_event_ids", queued_event_ids)

            # 4. 선점한 alert_events 기준 user_channel 조회
            user_channels = uow.alerts.list_user_channel_by_filter(
                alert_event_ids=queued_event_ids,
                status=AlertEventStatus.QUEUED,
            )

            event_ids_with_channel = {
                channel.alert_event_id
                for channel in user_channels
            }

            skipped_event_ids = [
                event.id
                for event in queued_events
                if event.id not in event_ids_with_channel
            ]

            # print("AlertEventChannel", user_channels)

            user_channels_by_event_id = {}

            for channel in user_channels:
                user_channels_by_event_id.setdefault(channel.alert_event_id, []).append(channel)

            # print("user_channels_by_event_id", user_channels_by_event_id)
            # 5. alert_deliveries 생성
            deliveries = []

            for event in queued_events:
                event_channels = user_channels_by_event_id.get(event.id, [])

                for channel in event_channels:
                    deliveries.append(
                        AlertDTO.AlertDeliveryCreate(
                            alert_event_id=event.id,
                            user_channel_id=channel.user_channel_id,
                            status=AlertDeliveryStatus.QUEUED,
                        )
                    )

            # print("deliveries", deliveries)
            if not deliveries:
                uow.alerts.update_alert_events_by_status(
                    alert_event_ids=queued_event_ids,
                    from_status=AlertEventStatus.QUEUED,
                    to_status=AlertEventStatus.SKIPPED,
                )
                uow.commit()

                return {
                    "selected_count": selected_count,
                    "queued_count": queued_count,
                    "delivery_count": 0,
                    "sent_count": 0,
                    "failed_count": 0,
                    "skipped_count": queued_count,
                }

            if skipped_event_ids:
                uow.alerts.update_alert_events_by_status(
                    alert_event_ids=skipped_event_ids,
                    from_status=AlertEventStatus.QUEUED,
                    to_status=AlertEventStatus.SKIPPED,
                )

            dispatched_event_ids = list({
                delivery.alert_event_id
                for delivery in deliveries
            })

            if dispatched_event_ids:
                uow.alerts.update_alert_events_by_status(
                    alert_event_ids=dispatched_event_ids,
                    from_status=AlertEventStatus.QUEUED,
                    to_status=AlertEventStatus.DISPATCHED,
                )

            skipped_count = len(skipped_event_ids)
            delivery_count = uow.alerts.add_alert_deliveries(deliveries)

            # print("delivery_count", delivery_count)

            # 6. alert_events DISPATCHED 처리
            uow.alerts.update_alert_events_by_status(
                alert_event_ids=queued_event_ids,
                from_status=AlertEventStatus.QUEUED,
                to_status=AlertEventStatus.DISPATCHED,
            )

            # 7. 방금 만든 delivery를 event/channel과 함께 조회
            alert_deliveries = uow.alerts.list_alert_delivery_from_ids(
                alert_event_ids=queued_event_ids,
                status=AlertDeliveryStatus.QUEUED,
            )

            alert_delivery_ids = [delivery.id for delivery in alert_deliveries]

            dispatch_targets = uow.alerts.list_alert_delivery_targets(
                alert_delivery_ids=alert_delivery_ids,
                status=AlertDeliveryStatus.QUEUED,
            )

            # print("alert_deliveries", alert_deliveries)
            # print("dispatch_targets", dispatch_targets)

            uow.commit()

        send_items: dict[str, list[ChannelDTO.ChannelSendItem]] = {}
        failed_delivery_ids: list[int] = []

        for target in dispatch_targets:
            if not target.address:
                failed_delivery_ids.append(target.alert_delivery_id)
                continue

            provider_code = target.channel_provider_code
            if provider_code not in self._channel_message_providers:
                failed_delivery_ids.append(target.alert_delivery_id)
                continue

            content = self._alert_message_builder.build(
                context=target.context or {},
                trigger_value=target.trigger_value,
                alert_event_id=target.alert_event_id,
            )

            message = ChannelDTO.ChannelMessage(
                target=target.address,
                title=content.title,
                body=content.body,
                data=content.data,
            )

            send_items.setdefault(provider_code, []).append(
                ChannelDTO.ChannelSendItem(
                    delivery_id=target.alert_delivery_id,
                    message=message
                )
            )

        send_results: list[AlertDTO.AlertDeliverySendResult] = []

        for provider_code, items in send_items.items():
            message_provider = self._channel_message_providers[provider_code]
            messages = [item.message for item in items]

            # print("message_provider", message_provider)
            # print("messages", messages)

            # results = []
            try:
                results = message_provider.send_messages(messages)
            except Exception as e:
                for item in items:
                    send_results.append(
                        AlertDTO.AlertDeliverySendResult(
                            alert_delivery_id=item.delivery_id,
                            success=False,
                            response_code=None,
                            response_body=str(e),
                        )
                    )
                continue

            # print("messages results", results)
            # fcm의 경우 send_each의 응답 순서 보장에 의존하는 구조이기 때문에 확인 필요
            # TODO: 추후 수동, 자동 재시도 정책
            if len(results) != len(items):
                # raise RuntimeError(
                #     f"invalid send result length provider={provider_code} "
                #     f"messages={len(items)} results={len(results)}"
                # )
                for item in items:
                    send_results.append(
                        AlertDTO.AlertDeliverySendResult(
                            alert_delivery_id=item.delivery_id,
                            success=False,
                            response_code=None,
                            response_body=(
                                f"invalid send result length provider={provider_code} "
                                f"messages={len(items)} results={len(results)}"
                            ),
                        )
                    )
                continue


            for idx, result in enumerate(results):
                delivery_id = items[idx].delivery_id

                send_results.append(
                    AlertDTO.AlertDeliverySendResult(
                        alert_delivery_id=delivery_id,
                        success=result.success,
                        response_code=None,
                        response_body=result.message_id if result.success else result.error,
                    )
                )

        for delivery_id in failed_delivery_ids:
            send_results.append(
                AlertDTO.AlertDeliverySendResult(
                    alert_delivery_id=delivery_id,
                    success=False,
                    response_code=None,
                    response_body="message provider or address not found",
                )
            )
        
        success_results = [result for result in send_results if result.success]
        failed_results = [result for result in send_results if not result.success]

        # print("success_results", success_results)
        # print("failed_results", failed_results)

        sent_count = len(success_results)
        failed_count = len(failed_results)

        with self._uow_factory() as uow:
            if success_results:
                uow.alerts.update_alert_deliveries_status(
                    send_results=success_results,
                    from_status=AlertDeliveryStatus.QUEUED,
                    to_status=AlertDeliveryStatus.SENT,
                    sent_at=utcnow(),
                )

            if failed_results:
                uow.alerts.update_alert_deliveries_status(
                    send_results=failed_results,
                    from_status=AlertDeliveryStatus.QUEUED,
                    to_status=AlertDeliveryStatus.FAILED,
                )

            uow.commit()

        return {
            "selected_count": selected_count,
            "queued_count": queued_count,
            "delivery_count": delivery_count,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
        }


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

            bucket_key = self._alert_bucket.get_alert_bucket_key(
                indicator=alert_snapshot.indicator,
                exchange_code=alert_snapshot.exchange_code,
                exchange_symbol=alert_snapshot.exchange_symbol,
                form_type=alert_snapshot.form_type,
                scope=alert_snapshot.scope,
                direction=alert_snapshot.direction,
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
        old_payload = self._alert_snapshot.get_alert(alert_id)
        if old_payload:
            old_bucket_key = old_payload.get("bucket_key")

            if old_bucket_key:
                self._alert_bucket.remove_alert(
                    bucket_key=old_bucket_key,
                    alert_id=alert_id,
                )

        if alert_snapshot is None:
            self._alert_snapshot.remove_alert(alert_id)
            return

        if alert_snapshot.status != AlertStatus.ACTIVE:
            self._alert_snapshot.remove_alert(alert_id)
            return

        payload = AlertRule.alert_snapshot_to_payload(alert_snapshot)

        bucket_key = self._alert_bucket.get_alert_bucket_key(
            indicator=alert_snapshot.indicator,
            exchange_code=alert_snapshot.exchange_code,
            exchange_symbol=alert_snapshot.exchange_symbol,
            form_type=alert_snapshot.form_type,
            scope=alert_snapshot.scope,
            direction=alert_snapshot.direction,
        )

        self._alert_bucket.add_alert(
            bucket_key=bucket_key,
            alert_id=alert_snapshot.alert_id,
        )

        payload["bucket_key"] = bucket_key

        self._alert_snapshot.upsert_alert(
            alert_id=alert_snapshot.alert_id,
            payload=payload,
        )

