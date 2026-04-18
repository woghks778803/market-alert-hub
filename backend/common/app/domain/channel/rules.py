from app.core.constants import ChannelCode
from app.domain.shared.errors import ValidationAppError

MAX_ACTIVE_CHANNELS_PER_USER = 5


def validate_user_config(code: ChannelCode, config: dict | None, user_schema: dict | None):
    # 간단 분기 + (옵션) JSON Schema 검증
    cfg = config or {}
    if code == ChannelCode.FCM and (not cfg.get("token") or not cfg.get("platform")):
        raise ValidationAppError("FCM config is required.", target="config")
    if code == ChannelCode.TELEGRAM and cfg.get("chat_id") in (None, ""):
        raise ValidationAppError(
            "Telegram config is required.", target="config"
        )
    if code == ChannelCode.DISCORD and not cfg.get("webhook_url"):
        raise ValidationAppError(
            "Discord config is required.", target="config"
        )
    # user_schema가 있으면 fastjsonschema로 추가 검증 가능
