import asyncio
from typing import Any
from .exchange import run_stream_marketdata_loop
from app.core.constants import CURSOR, TICKERS


async def run_stream_marketdata_main_loop(
    *,
    stop_event,
    checkpoint_store: Any,
    ctx,
    reconnect_backoff_sec: int,
):
    tasks: dict[str, asyncio.Task] = {}
    cfg = ctx.config
    key_prefix = f"{cfg.app_name}:{cfg.deploy_env}"
    catalog = ctx.facade.active_catalog  # RedisActiveMarketCatalog
    ws_factory = ctx.ws_facs_register

    try:
        while not stop_event.is_set():
            exchanges = await catalog.get_exchanges_snap()
            active_codes = set(exchanges.keys())
            current_codes = set(tasks.keys())

            # --- 추가 ---
            for code in active_codes - current_codes:
                if code not in ws_factory:
                    continue

                task = asyncio.create_task(
                    run_stream_marketdata_loop(
                        stop_event=stop_event,
                        checkpoint_store=checkpoint_store,
                        ctx=ctx,
                        exchange_code=code,
                        reconnect_backoff_sec=reconnect_backoff_sec,
                        checkpoint_key=f"{key_prefix}:{CURSOR}:{code}:{TICKERS}",
                    )
                )
                tasks[code] = task

            # --- 제거 ---
            for code in current_codes - active_codes:
                task = tasks.pop(code)
                task.cancel()

            await asyncio.sleep(1)

    finally:
        for task in tasks.values():
            task.cancel()
        await asyncio.gather(*tasks.values(), return_exceptions=True)
