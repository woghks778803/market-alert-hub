from typing import Any
from datetime import datetime
from dataclasses import dataclass
from app.core.constants import AlertStatus, AlertScope

@dataclass(slots=True, frozen=True)
class AlertSummary:
    total_count: int
    active_count: int
    paused_count: int

@dataclass(slots=True)
class AlertSimple:
    id: int
    alert_type_id: int
    name: str

    status: AlertStatus

    timezone: str
    timeframe: str | None
    period: int | None
    params: dict
    throttle_seconds: int
    is_once: bool
    valid_from: datetime | None
    valid_to: datetime | None
    updated_at: datetime

    exchange_instrument_id: int
    exchange_symbol: str
    ei_is_active: bool
    exchange_code: str
    exchange_name: str
    e_is_active: bool


@dataclass(slots=True, frozen=True)
class Alert:
    id: int

    user_id: int
    alert_type_id: int
    exchange_instrument_id: int | None

    name: str
    status: AlertStatus

    timezone: str
    timeframe: str | None
    period: int | None

    params: dict[str, Any]

    throttle_seconds: int

    valid_from: datetime | None
    valid_to: datetime | None

    is_once: bool

    # 수정 주의
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_fired_at: datetime | None = None
    deleted_at: datetime | None = None

@dataclass(slots=True, frozen=True)
class AlertCreate:
    user_id: int
    alert_type_id: int
    exchange_instrument_id: int | None

    name: str
    timezone: str

    status: AlertStatus

    timeframe: str | None
    period: int | None

    params: dict[str, Any]

    throttle_seconds: int

    valid_from: datetime | None
    valid_to: datetime | None

    is_once: bool

    last_fired_at: datetime | None = None
    deleted_at: datetime | None = None

    

@dataclass(slots=True, frozen=True)
class AlertType:
    id: int
    code: str
    name: str

    scope: AlertScope
    indicator: str
    direction: str | None
    form_type: str
    param_schema: dict

    sort_order: int
    is_active: bool
    
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


@dataclass(slots=True)
class AlertSnapshot:
    alert_id: int
    user_id: int

    status: AlertStatus

    alert_type_id: int
    alert_type_code: str
    scope: AlertScope
    indicator: str
    direction: str
    form_type: str

    exchange_instrument_id: int
    exchange_code: str
    exchange_symbol: str

    timeframe: str | None
    period: int | None
    params: dict

    throttle_seconds: int
    valid_from: datetime | None
    valid_to: datetime | None
    is_once: bool
    last_fired_at: datetime | None

