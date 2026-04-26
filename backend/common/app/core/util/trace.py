from uuid import uuid4
from contextvars import ContextVar, Token

_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)


def get_trace_id() -> str:
    tid = _trace_id.get()
    if tid:
        return tid
    tid = str(uuid4())
    _trace_id.set(tid)
    return tid


def set_trace_id(value: str | None) -> Token[str | None]:
    return _trace_id.set(value)


def clear_trace_id() -> None:
    _trace_id.set(None)
