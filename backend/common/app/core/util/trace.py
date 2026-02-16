from uuid import uuid4
from contextvars import ContextVar, Token

# import threading, contextvars, asyncio

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


# def _dbg(tag: str):
#     try:
#         task = asyncio.current_task()
#         task_id = id(task) if task else None
#     except RuntimeError:
#         task_id = None
#     ctx_id = id(contextvars.copy_context())
#     print(f"[{tag}] thread={threading.get_ident()} task={task_id} ctx={ctx_id}")

# def reset_trace_id(token):
#     _dbg("RESET:before")
#     print("[RESET] token_id=", id(token))
#     _trace_id.reset(token)
#     _dbg("RESET:after")
