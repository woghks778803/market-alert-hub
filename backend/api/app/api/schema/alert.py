from typing import Literal, Any
from datetime import datetime
from decimal import Decimal
from pydantic import AwareDatetime

from app.core.constants import AlertEventStatus, AlertStatus, AlertFormType, IndicatorType, DirectionType, ThrottleTimeframe
from app.api.schema.base import ApiResponseModel, ApiRequestModel


class AlertIn(ApiRequestModel):
    name: str
    exchange_instrument_id: int | None = None
    alert_type_id: int

    is_once: bool
    status: AlertStatus

    throttle_timeframe: ThrottleTimeframe  
    timezone: str

    use_validity: bool
    valid_from: AwareDatetime | None = None
    valid_to: AwareDatetime | None = None

    params: dict[str, Any]


class AlertStatusIn(ApiRequestModel):
    status: AlertStatus


class SimpleOk(ApiResponseModel):
    ok: bool = True


class AlertSummaryRead(ApiResponseModel):
    total_count: int
    active_count: int
    paused_count: int


class AlertRead(ApiResponseModel):
    id: int
    alert_type_id: int
    name: str
    status: str

    timezone: str
    params: dict

    throttle_seconds: int
    is_once: bool
    valid_from: datetime | None
    valid_to: datetime | None
    updated_at: datetime

    exchange_instrument_id: int
    exchange_symbol: str
    exchange_code: str
    exchange_name: str
    ei_is_active: bool
    e_is_active: bool


class AlertLogRead(ApiResponseModel):
    alert_event_id: int
    alert_id: int
    title: str
    body: str
    exchange_code: str
    exchange_symbol: str
    status: AlertEventStatus
    detected_at: datetime


class AlertTypeRead(ApiResponseModel):
    id: int
    code: str
    name: str

    indicator: IndicatorType
    direction: DirectionType | None
    form_type: AlertFormType
    param_schema: dict
    

