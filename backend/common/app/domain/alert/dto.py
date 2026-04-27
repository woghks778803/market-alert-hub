from typing import Any
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass
from app.core.constants import AlertStatus, AlertEventStatus, AlertDeliveryStatus, ConditionType, AlertFormType, IndicatorType, DirectionType

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

    params: dict

    is_once: bool
    throttle_seconds: int
    
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

    params: dict[str, Any]

    is_once: bool
    throttle_seconds: int

    valid_from: datetime | None
    valid_to: datetime | None

    created_at: datetime | None
    updated_at: datetime | None
    last_fired_at: datetime | None
    deleted_at: datetime | None

@dataclass(slots=True, frozen=True)
class AlertCreate:
    user_id: int
    alert_type_id: int
    exchange_instrument_id: int | None

    name: str
    timezone: str
    status: AlertStatus

    params: dict[str, Any]

    is_once: bool
    throttle_seconds: int

    valid_from: datetime | None
    valid_to: datetime | None

    last_fired_at: datetime | None = None
    deleted_at: datetime | None = None

    

@dataclass(slots=True, frozen=True)
class AlertType:
    id: int
    code: str
    name: str

    scope: ConditionType
    indicator: IndicatorType
    direction: DirectionType | None
    form_type: AlertFormType
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

    alert_name: str

    status: AlertStatus

    alert_type_id: int
    alert_type_code: str
    alert_type_name: str

    scope: ConditionType
    indicator: IndicatorType
    direction: DirectionType
    form_type: AlertFormType

    exchange_instrument_id: int
    exchange_code: str
    exchange_symbol: str

    params: dict
    param_schema: dict

    is_once: bool
    throttle_seconds: int
    valid_from: datetime | None
    valid_to: datetime | None
    last_fired_at: datetime | None


@dataclass(slots=True, frozen=True)
class AlertEvent:
    id: int
    alert_id: int
    exchange_instrument_id: int | None

    status: AlertEventStatus

    detected_at: datetime
    
    trigger_value: Decimal | None
    context: dict | None
    dedup_key: str
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True, frozen=True)
class AlertEventCreate:
    alert_id: int
    exchange_instrument_id: int | None
    detected_at: datetime
    trigger_value: Decimal | None
    context: dict | None
    dedup_key: str

    status: AlertEventStatus = AlertEventStatus.PENDING


@dataclass(slots=True, frozen=True)
class AlertEventChannel:
    alert_event_id: int
    alert_id: int
    user_id: int
    user_channel_id: int
    channel_provider_id: int
    channel_provider_code: str
    address: str
    config: dict | None

@dataclass(slots=True, frozen=True)
class AlertDelivery:
    id: int
    alert_event_id: int
    user_channel_id: int
    status: AlertDeliveryStatus
    sent_at: datetime | None
    response_code: int | None
    response_body: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True, frozen=True)
class AlertDeliveryCreate:
    alert_event_id: int
    user_channel_id: int 

    status: AlertDeliveryStatus = AlertDeliveryStatus.QUEUED


@dataclass(slots=True, frozen=True)
class AlertDeliveryTarget:
    alert_delivery_id: int
    alert_event_id: int
    user_channel_id: int
    delivery_status: AlertDeliveryStatus

    alert_id: int
    exchange_instrument_id: int | None
    trigger_value: Decimal | None
    context: dict | None
    detected_at: datetime

    channel_provider_id: int
    address: str
    channel_config: dict | None
    channel_provider_code: str

@dataclass(slots=True, frozen=True)
class AlertDeliverySendResult:
    alert_delivery_id: int
    success: bool
    response_code: int | None = None
    response_body: str | None = None

@dataclass(slots=True, frozen=True)
class AlertMessageContent:
    title: str
    body: str
    data: dict[str, str]
