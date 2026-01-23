import logging
from typing import Any, Mapping

from app.core.constants import OutboxEventType, SNAP, META, TMP, LOCK, STREAM
from app.runtime.app_context import WorkerContext
from app.util.utils import (
    require,
    try_acquire_lock,
    release_lock,
    load_snap_json_map,
    load_ticker_1s_ticks,
)
from app.exception_handlers import (
    RetryHandler,
    SkipHandler,
    FatalHandler,
    ValidationHandler,
)

logger = logging.getLogger(__name__)


def handle_persist_snapshots(
    ctx: WorkerContext,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    interval_sec = int(require(payload, "interval_sec", target="payload.interval_sec"))
    slot = int(require(payload, "slot", target="payload.slot"))
    job_config = ctx.config.worker_jobs[OutboxEventType.PERSIST_SNAPSHOTS.value]
    app_name = ctx.config.app_name
    deploy_env = ctx.config.deploy_env
    run_key = job_config["run_key"]

    # Prefer explicit bucket boundaries if provided; otherwise derive deterministically.
    bucket_end_epoch = slot * interval_sec
    bucket_start_epoch = bucket_end_epoch - interval_sec

    if interval_sec <= 0:
        raise ValidationHandler(
            "interval_sec must be positive",
            target="interval_sec",
            meta={"interval_sec": interval_sec},
        )

    if bucket_start_epoch >= bucket_end_epoch:
        raise SkipHandler(
            "invalid bucket range",
            target="interval_sec",
            meta={
                "interval_sec": interval_sec,
                "slot": slot,
                "bucket_start_epoch": bucket_start_epoch,
                "bucket_end_epoch": bucket_end_epoch,
            },
        )

    r = ctx.redis_client.conn()
    lock_key = f"{app_name}:{deploy_env}:{LOCK}:{run_key}:{slot}:{interval_sec}"
    token = try_acquire_lock(
        ctx.redis_client, key=lock_key, ttl_sec=max(30, min(interval_sec, 300))
    )
    if not token:
        raise SkipHandler("locked")

    try:
        logger.info(
            "persist snapshots start interval_sec=%s slot=%s range=[%s,%s)",
            interval_sec,
            slot,
            bucket_start_epoch,
            bucket_end_epoch,
        )

        exchanges = load_snap_json_map(
            ctx.redis_client,
            f"{app_name}:{deploy_env}:{SNAP}:{OutboxEventType.SYNC_EXCHANGES.value}",
        )

        for exchange_code, exchange_data in exchanges.items():
            symbols = load_snap_json_map(
                ctx.redis_client,
                f"{app_name}:{deploy_env}:{SNAP}:{OutboxEventType.SYNC_SYMBOLS.value}:{exchange_code}",
            )

            if interval_sec == 60:
                upsert_snapshots_1m = []
                no_tick_payloads = []
                for symbol, payload in symbols.items():
                    key = f"{app_name}:{deploy_env}:{STREAM}:ticker:{exchange_code}:{symbol}"

                    symbol_ticks = load_ticker_1s_ticks(
                        ctx.redis_client,
                        key=key,
                        bucket_start_epoch=bucket_start_epoch,
                        bucket_end_epoch=bucket_end_epoch,
                    )
                    # print(key)
                    # print(payload)
                    # print(symbol_ticks)

                    if symbol_ticks:
                        upsert_snapshots_1m.append(
                            ctx.svcs.markets.normalize_snapshots_1m(
                                payload,
                                symbol_ticks,
                                bucket_start_epoch=bucket_start_epoch,
                            )
                        )
                    else:
                        no_tick_payloads.append(payload)

                if no_tick_payloads:
                    upsert_snapshots_1m.extend(
                        ctx.svcs.markets.normalize_empty_snapshots_1m(
                            no_tick_payloads, bucket_start_epoch
                        )
                    )
                print(
                    f"persist_snapshots: upsert {len(upsert_snapshots_1m)} snapshots for exchange {exchange_code}"
                )
                print(upsert_snapshots_1m)

                ctx.svcs.markets.ensure_snapshots_1m(upsert_snapshots_1m)
            elif interval_sec == 60 * 60:
                pass  # 1시간틱 롤업 처리
            elif interval_sec == 24 * 60 * 60:
                pass  # 1일틱 롤업 처리

        result = {
            "interval_sec": interval_sec,
            "slot": slot,
            "bucket_start_epoch": bucket_start_epoch,
            "bucket_end_epoch": bucket_end_epoch,
            "status": "TODO",
        }
        logger.info(
            "persist snapshots done interval_sec=%s slot=%s", interval_sec, slot
        )
        return result

    except Exception as e:
        raise FatalHandler(
            "persist_snapshots_fatal",
            meta={"error": str(e), "interval_sec": interval_sec, "slot": slot},
        ) from e
    finally:
        release_lock(ctx.redis_client, lock_key, token)
