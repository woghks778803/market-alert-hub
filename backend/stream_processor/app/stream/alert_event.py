import asyncio
import socket
from typing import Any

from app.core.constants import StreamType

async def run_alert_event_loop(
    *,
    stop_event: asyncio.Event,
    ctx: Any,
) -> None:
    """
    Redis Stream alert_event를 소비해서 RDB alert_events에 bulk insert한다.

    역할:
    - XREADGROUP
    - stream payload p json.loads()
    - RDB bulk insert
    - 성공 후 XACK
    """
    svcs = ctx.svcs
    batch_size = ctx.config.alert_event_batch_size
    block_ms = ctx.config.alert_event_block_ms

    consumer_name = f"{ctx.config.service_name}:{StreamType.PERSIST_ALERT_EVENTS.value}:{socket.gethostname()}"
    await svcs.alert_event.ensure_persist_group()

    try:
        while not stop_event.is_set():
            processed = await svcs.alerts.persist_alert_events(
                consumer_name=consumer_name,
                batch_size=batch_size,
                block_ms=block_ms,
            )

            if processed <= 0:
                await asyncio.sleep(0.2)

    except asyncio.CancelledError:
        raise
