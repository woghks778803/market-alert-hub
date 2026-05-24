import logging, sys, json
from typing import Any
from .util.datetime import utcnow, ISO_FMT

_CONFIGURED = False  # 멱등 플래그

def resolve_log_level(log_level: str | None, default: int = logging.INFO) -> int:
    if not log_level:
        return default

    level = getattr(logging, log_level.upper(), None)

    if isinstance(level, int):
        return level

    return default

def setup_logging(level: int = logging.INFO, *, service: str = "app") -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONLogFormatter(service=service))
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]
    _CONFIGURED = True


class JSONLogFormatter(logging.Formatter):
    def __init__(self, *, service: str = "app") -> None:
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "service": self.service,
            "message": record.getMessage(),
            "time": utcnow().strftime(ISO_FMT),
        }
        if hasattr(record, "request_id"):
            payload["request_id"] = getattr(record, "request_id")
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)
