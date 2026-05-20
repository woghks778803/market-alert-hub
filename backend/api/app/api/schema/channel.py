from pydantic import Field

from app.api.schema.base import ApiResponseModel, ApiRequestModel


class ChannelRead(ApiResponseModel):
    id: int
    code: str
    name: str
    description: str | None



