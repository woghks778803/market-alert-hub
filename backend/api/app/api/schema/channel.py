from pydantic import BaseModel, ConfigDict, Field

_model_cfg = ConfigDict(from_attributes=True, use_enum_values=True)

class ChannelCreate(BaseModel):
    channel_provider_id: int = Field(..., description="채널 타입")
    config: dict | None = Field(None, description="채널별 인증/설정 정보")

class ChannelProviderBase(BaseModel):
    model_config = _model_cfg
    id: int
    code: str
    name: str

class ChannelRead(BaseModel):
    model_config = _model_cfg

    id: int
    channel_provider: ChannelProviderBase
    config: dict | None
    verified_at: str | None
    is_valid: bool



