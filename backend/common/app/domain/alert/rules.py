from typing import Any
from app.core.util.serialization import json_safe
from app.core.constants import AlertStatus
import app.domain.alert.dto as AlertDTO

MAX_ARCHIVED_ALERTS_PER_USER = 200
MAX_NON_ARCHIVED_ALERTS_PER_USER = 30
MAX_ACTIVE_ALERTS_PER_USER = 5

def alert_snapshot_to_payload(
    alert_snapshot: AlertDTO.AlertSnapshot,
) -> dict[str, Any]:
    """
    전체 활성 알림 동기화에서 조회한 AlertSnapshot을
    Redis snapshot에 넣을 payload로 변환.
    """
    return {
        "alert_id": json_safe(alert_snapshot.alert_id),
        "user_id": json_safe(alert_snapshot.user_id),

        "status": json_safe(alert_snapshot.status),

        "alert_type_id": json_safe(alert_snapshot.alert_type_id),
        "alert_type_code": json_safe(alert_snapshot.alert_type_code),
        "scope": json_safe(alert_snapshot.scope),
        "indicator": json_safe(alert_snapshot.indicator),
        "direction": json_safe(alert_snapshot.direction),
        "form_type": json_safe(alert_snapshot.form_type),

        "exchange_instrument_id": json_safe(alert_snapshot.exchange_instrument_id),
        "exchange_code": json_safe(alert_snapshot.exchange_code),
        "exchange_symbol": json_safe(alert_snapshot.exchange_symbol),

        "params": json_safe(alert_snapshot.params or {}),

        "is_once": json_safe(alert_snapshot.is_once),
        "throttle_seconds": json_safe(alert_snapshot.throttle_seconds),
        "valid_from": json_safe(alert_snapshot.valid_from),
        "valid_to": json_safe(alert_snapshot.valid_to),
        "last_fired_at": json_safe(alert_snapshot.last_fired_at),

        "bucket_key": None,
    }

# TODO: 미사용
def alert_to_snapshot(
    alert: AlertDTO.Alert,
    alert_type: AlertDTO.AlertType,
) -> AlertDTO.AlertSnapshot:
    return AlertDTO.AlertSnapshot(
        alert_id=alert.id,
        user_id=alert.user_id,
        alert_type_id=alert.alert_type_id,
        alert_type_code=alert_type.code,
        indicator=alert_type.indicator,
        direction=alert_type.direction,
        form_type=alert_type.form_type,
        exchange_instrument_id=alert.exchange_instrument_id,
        exchange_code=alert.exchange_code,
        exchange_symbol=alert.exchange_symbol,
        params=alert.params,
        throttle_seconds=alert.throttle_seconds,
        valid_from=alert.valid_from,
        valid_to=alert.valid_to,
        is_once=alert.is_once,
        last_fired_at=alert.last_fired_at,
    )
