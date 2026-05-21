from pydantic import Field
from datetime import datetime

from app.api.schema.base import ApiResponseModel, ApiRequestModel


class ChannelRead(ApiResponseModel):
    id: int
    code: str
    name: str
    description: str | None

    is_active: bool


class UserChannelRead(ApiResponseModel):
    id: int
    user_id: int
    channel_provider_id: int

    verified_at: datetime | None
    created_at: datetime 
    updated_at: datetime
    deleted_at: datetime | None

    is_active: bool

