from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

_model_cfg = ConfigDict(from_attributes=True, use_enum_values=True)

class ApiRequestModel(BaseModel):
    pass

class ApiResponseModel(BaseModel):
    model_config = _model_cfg

    @field_validator("*", mode="before")
    @classmethod
    def attach_utc_timezone(cls, value: Any) -> Any:
        if not isinstance(value, datetime):
            return value

        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)

            return value.astimezone(timezone.utc)

        return value