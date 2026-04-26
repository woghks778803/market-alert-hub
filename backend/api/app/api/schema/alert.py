from typing import Literal, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.core.constants import AlertStatus, AlertFormType, IndicatorType, DirectionType, ThrottleTimeframe

_model_cfg = ConfigDict(from_attributes=True, use_enum_values=True)

class SimpleOk(BaseModel):
    ok: bool = True

class AlertIn(BaseModel):
    model_config = _model_cfg

    name: str
    exchange_instrument_id: int | None = None
    alert_type_id: int

    is_once: bool
    status: AlertStatus

    throttle_timeframe: ThrottleTimeframe  
    timezone: str

    use_validity: bool
    valid_from: datetime | None = None
    valid_to: datetime | None = None

    params: dict[str, Any]

class AlertStatusIn(BaseModel):
    model_config = _model_cfg

    status: AlertStatus

class AlertSummaryRead(BaseModel):
    model_config = _model_cfg

    total_count: int
    active_count: int
    paused_count: int

class AlertRead(BaseModel):
    model_config = _model_cfg

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


class AlertTypeRead(BaseModel):
    id: int
    code: str
    name: str

    indicator: IndicatorType
    direction: DirectionType | None
    form_type: AlertFormType
    param_schema: dict
    
    model_config = _model_cfg

