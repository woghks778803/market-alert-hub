import json
import base64
from datetime import datetime
from typing import Any
from decimal import Decimal, InvalidOperation

from app.core.util.serialization import json_safe
from app.core.constants import AlertSort, AlertStatus, AlertEventStatus, AlertFormType, IndicatorType, DirectionType
import app.domain.alert.dto as AlertDTO

MAX_ARCHIVED_ALERTS_PER_USER = 200
MAX_NON_ARCHIVED_ALERTS_PER_USER = 30
MAX_ACTIVE_ALERTS_PER_USER = 5

def decode_alert_cursor(cursor: str) -> AlertDTO.AlertListCursor:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    payload = json.loads(raw)

    return AlertDTO.AlertListCursor(
        sort=AlertSort(payload["sort"]),
        alert_id=int(payload["alert_id"]),
        updated_at=(
            datetime.fromisoformat(payload["updated_at"])
            if payload.get("updated_at")
            else None
        ),
        created_at=(
            datetime.fromisoformat(payload["created_at"])
            if payload.get("created_at")
            else None
        ),
        exchange_symbol=payload.get("exchange_symbol"),
        status=(
            AlertStatus(payload["status"])
            if payload.get("status")
            else None
        ),
    )

def decode_alert_log_cursor(cursor: str) -> AlertDTO.AlertLogListCursor:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    payload = json.loads(raw)

    return AlertDTO.AlertLogListCursor(
        alert_event_id=int(payload["alert_event_id"]),
        cursor_at=(
            datetime.fromisoformat(payload["cursor_at"])
            if payload.get("cursor_at")
            else None
        ),
    )

def make_alert_cursor(*, sort: AlertSort, item) -> str:
    payload = {
        "sort": sort.value,
        "alert_id": item.alert_id,
    }

    if sort == AlertSort.RECENT_CREATED:
        payload["created_at"] = item.created_at.isoformat()

    elif sort == AlertSort.MARKET_ASC:
        payload["exchange_symbol"] = item.exchange_symbol

    elif sort == AlertSort.STATUS:
        payload["status"] = item.status.value
        payload["updated_at"] = item.updated_at.isoformat()

    else:
        payload["updated_at"] = item.updated_at.isoformat()

    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return base64.urlsafe_b64encode(raw.encode()).decode()

def make_alert_log_cursor(*, item) -> str: 
    cursor_at = item.detected_at

    payload = {
        "alert_event_id": item.alert_event_id,
        "cursor_at": cursor_at.isoformat(),
    }

    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return base64.urlsafe_b64encode(raw.encode()).decode()

def make_alert_log(
    *,
    event: AlertDTO.AlertEvent,
    content: AlertDTO.AlertMessageContent,
) -> AlertDTO.AlertLog:
    context = event.context or {}

    return AlertDTO.AlertLog(
        alert_event_id=event.id,
        alert_id=event.alert_id,
        title=content.title,
        body=content.body,
        exchange_code=context.get("exchange_code"),
        exchange_symbol=context.get("exchange_symbol"),
        status=event.status,
        detected_at=event.detected_at,
    )

def alert_snapshot_to_payload(
    alert_snapshot: AlertDTO.AlertSnapshot,
) -> dict[str, Any]:
    """
    전체 활성 알림 동기화에서 조회한 AlertSnapshot을
    Redis snapshot에 넣을 payload로 변환.
    """
    return {
        "alert_id": json_safe(alert_snapshot.alert_id),
        "alert_name": json_safe(alert_snapshot.alert_name),
        "user_id": json_safe(alert_snapshot.user_id),

        "status": json_safe(alert_snapshot.status),

        "alert_type_id": json_safe(alert_snapshot.alert_type_id),
        "alert_type_code": json_safe(alert_snapshot.alert_type_code),
        "alert_type_name": json_safe(alert_snapshot.alert_type_name),

        "scope": json_safe(alert_snapshot.scope),
        "indicator": json_safe(alert_snapshot.indicator),
        "direction": json_safe(alert_snapshot.direction),
        "form_type": json_safe(alert_snapshot.form_type),

        "exchange_instrument_id": json_safe(alert_snapshot.exchange_instrument_id),
        "exchange_code": json_safe(alert_snapshot.exchange_code),
        "exchange_name": json_safe(alert_snapshot.exchange_name),
        "exchange_symbol": json_safe(alert_snapshot.exchange_symbol),

        "params": json_safe(alert_snapshot.params or {}),
        "param_schema": json_safe(alert_snapshot.param_schema or {}),

        "is_once": json_safe(alert_snapshot.is_once),
        "throttle_seconds": json_safe(alert_snapshot.throttle_seconds),
        "valid_from": json_safe(alert_snapshot.valid_from),
        "valid_to": json_safe(alert_snapshot.valid_to),
        "last_fired_at": json_safe(alert_snapshot.last_fired_at),

        "bucket_key": None,
    }

class AlertMessageBuilder:
    def __init__(self):
        self._form_builders = {
            AlertFormType.THRESHOLD.value: ThresholdMessageBuilder(),
            AlertFormType.RANGE.value: RangeMessageBuilder(),
            AlertFormType.PERCENT.value: PercentMessageBuilder(),
            AlertFormType.CROSS.value: CrossMessageBuilder(),
            AlertFormType.BAND.value: BandMessageBuilder(),
            AlertFormType.PATTERN.value: PatternMessageBuilder(),
        }
        self._default_builder = DefaultMessageBuilder()

    def build(
        self,
        *,
        context: dict,
        trigger_value,
        alert_event_id: int,
    ) -> AlertDTO.AlertMessageContent:
        title = self._make_title(context)

        form_type = str(context.get("form_type") or "")
        
        builder = self._form_builders.get(form_type, self._default_builder)

        trigger_value

        body = builder.build_body(
            context=context,
            trigger_value=trigger_value,
        )

        return AlertDTO.AlertMessageContent(
            title=title,
            body=body,
            data={
                "alert_event_id": str(alert_event_id),
            },
        )

    def _make_title(self, context: dict) -> str:
        title = context.get("alert_name")

        title = str(title).strip()
        title = " ".join(title.split())

        if not title:
            return "알림"

        return title[:40]

class AlertMessageBuildHelper:
    @staticmethod
    def get_symbol(context: dict) -> str:
        return str(context.get("exchange_symbol") or "대상")

    @staticmethod
    def get_alert_type_name(context: dict) -> str:
        return str(context.get("alert_type_name") or "알림")

    @staticmethod
    def get_param_value(context: dict, key: str):
        params = context.get("params") or {}
        return params.get(key)

    @staticmethod
    def get_field_label(context: dict, key: str) -> str:
        schema = context.get("param_schema") or {}
        fields = schema.get("fields") or []

        for field in fields:
            if field.get("key") == key:
                return str(field.get("label") or key)

        return key

    @staticmethod
    def make_base_body(context: dict) -> str:
        symbol = AlertMessageBuildHelper.get_symbol(context)
        alert_type_name = AlertMessageBuildHelper.get_alert_type_name(context)

        return f"{symbol} [{alert_type_name}] 조건이 발생했습니다."

    @staticmethod
    def append_parts(body: str, parts: list[str]) -> str:
        if not parts:
            return body

        return body + " " + ", ".join(parts)

    @staticmethod
    def append_trigger_value(parts: list[str], trigger_value) -> None:
        if trigger_value is not None:
            parts.append(f"발생값: {trigger_value}")

    @staticmethod
    def format_value(value) -> str:
        if value is None:
            return ""

        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return str(value)

        normalized = decimal_value.normalize()

        # 1E+3 같은 과학적 표기 방지
        text = format(normalized, "f")

        # 소수점 뒤 0 제거
        if "." in text:
            text = text.rstrip("0").rstrip(".")

        return text

class ThresholdMessageBuilder:
    def build_body(self, *, context: dict, trigger_value) -> str:
        body = AlertMessageBuildHelper.make_base_body(context)

        parts = []

        threshold = AlertMessageBuildHelper.get_param_value(context, AlertFormType.THRESHOLD.value)
        if threshold is not None:
            label = AlertMessageBuildHelper.get_field_label(context, AlertFormType.THRESHOLD.value)
            parts.append(f"{label}: {threshold}")

        trigger_text = AlertMessageBuildHelper.format_value(trigger_value)
        AlertMessageBuildHelper.append_trigger_value(parts, trigger_text)

        return AlertMessageBuildHelper.append_parts(body, parts)

class RangeMessageBuilder:
    def build_body(self, *, context: dict, trigger_value) -> str:
        body = AlertMessageBuildHelper.make_base_body(context)

        parts = []

        for key in ("min", "max", "min_value", "max_value"):
            value = AlertMessageBuildHelper.get_param_value(context, key)
            if value is None:
                continue

            label = AlertMessageBuildHelper.get_field_label(context, key)
            parts.append(f"{label}: {value}")

        trigger_text = AlertMessageBuildHelper.format_value(trigger_value)
        AlertMessageBuildHelper.append_trigger_value(parts, trigger_text)

        return AlertMessageBuildHelper.append_parts(body, parts)

class PercentMessageBuilder:
    def build_body(self, *, context: dict, trigger_value) -> str:
        body = AlertMessageBuildHelper.make_base_body(context)

        parts = []

        threshold = AlertMessageBuildHelper.get_param_value(context, AlertFormType.PERCENT.value)
        if threshold is not None:
            label = AlertMessageBuildHelper.get_field_label(context, AlertFormType.PERCENT.value)
            parts.append(f"{label}: {threshold}%")

        trigger_text = AlertMessageBuildHelper.format_value(trigger_value)
        AlertMessageBuildHelper.append_trigger_value(parts, trigger_text)

        return AlertMessageBuildHelper.append_parts(body, parts)

class CrossMessageBuilder:
    def build_body(self, *, context: dict, trigger_value) -> str:
        body = AlertMessageBuildHelper.make_base_body(context)

        parts = []

        for key in ("base", "base_value", "signal", "target"):
            value = AlertMessageBuildHelper.get_param_value(context, key)
            if value is None:
                continue

            label = AlertMessageBuildHelper.get_field_label(context, key)
            parts.append(f"{label}: {value}")

        trigger_text = AlertMessageBuildHelper.format_value(trigger_value)
        AlertMessageBuildHelper.append_trigger_value(parts, trigger_text)

        return AlertMessageBuildHelper.append_parts(body, parts)

class BandMessageBuilder:
    def build_body(self, *, context: dict, trigger_value) -> str:
        body = AlertMessageBuildHelper.make_base_body(context)

        parts = []

        for key in ("period", "stddev", "band_value", "target_band"):
            value = AlertMessageBuildHelper.get_param_value(context, key)
            if value is None:
                continue

            label = AlertMessageBuildHelper.get_field_label(context, key)
            parts.append(f"{label}: {value}")

        trigger_text = AlertMessageBuildHelper.format_value(trigger_value)
        AlertMessageBuildHelper.append_trigger_value(parts, trigger_text)

        return AlertMessageBuildHelper.append_parts(body, parts)

class PatternMessageBuilder:
    def build_body(self, *, context: dict, trigger_value) -> str:
        body = AlertMessageBuildHelper.make_base_body(context)

        parts = []

        pattern = AlertMessageBuildHelper.get_param_value(context, AlertFormType.PATTERN.value)
        if pattern is not None:
            label = AlertMessageBuildHelper.get_field_label(context, AlertFormType.PATTERN.value)
            parts.append(f"{label}: {pattern}")

        trigger_text = AlertMessageBuildHelper.format_value(trigger_value)
        AlertMessageBuildHelper.append_trigger_value(parts, trigger_text)

        return AlertMessageBuildHelper.append_parts(body, parts)

class DefaultMessageBuilder:
    def build_body(self, *, context: dict, trigger_value) -> str:
        body = AlertMessageBuildHelper.make_base_body(context)

        schema = context.get("param_schema") or {}
        fields = schema.get("fields") or []

        parts = []

        for field in sorted(fields, key=lambda item: item.get("order", 999)):
            key = field.get("key")
            if not key:
                continue

            value = AlertMessageBuildHelper.get_param_value(context, key)
            if value is None:
                continue

            label = field.get("label") or key
            parts.append(f"{label}: {value}")

        trigger_text = AlertMessageBuildHelper.format_value(trigger_value)
        AlertMessageBuildHelper.append_trigger_value(parts, trigger_text)

        return AlertMessageBuildHelper.append_parts(body, parts)