from app.domain.shared.errors import ValidationAppError

MAX_CHANNELS_PER_USER = 5


def validate_user_config(code: str, config: dict | None, user_schema: dict | None):
    # 간단 분기 + (옵션) JSON Schema 검증
    cfg = config or {}
    if code == "FCM" and not cfg.get("token"):
        raise ValidationAppError("FCM config.token is required.", target="config")
    if code == "TELEGRAM" and cfg.get("chat_id") in (None, ""):
        raise ValidationAppError(
            "Telegram config.chat_id is required.", target="config"
        )
    if code == "DISCORD" and not cfg.get("webhook_url"):
        raise ValidationAppError(
            "Discord config.webhook_url is required.", target="config"
        )
    # user_schema가 있으면 fastjsonschema로 추가 검증 가능
