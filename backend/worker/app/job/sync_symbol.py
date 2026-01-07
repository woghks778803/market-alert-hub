from typing import Any, Callable, Mapping
from app.runtime.app_context import WorkerContext

def handle_sync_symbols(
    ctx: WorkerContext,
    payload: Mapping[str, Any],
) -> Any:
    return