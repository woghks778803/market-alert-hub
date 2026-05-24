import json
import logging
from typing import Any, Mapping

from app.core.util.serialization import json_safe
from app.core.util.datetime import utcnow, datetime_to_epoch_ms
from app.core.constants import OutboxEventType, BUCKET, SNAP, META, TMP, LOCK, INDEX
from app.runtime.app_context import WorkerContext
from app.util.utils import require, try_acquire_lock, release_lock
from app.exception_handlers import SkipHandler, FatalHandler, RetryHandler

logger = logging.getLogger(__name__)


def handle_sync_alerts(
    ctx: WorkerContext,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    redis_key_prefix = f"{{{ctx.config.key_prefix}}}"
    started_at = utcnow()

    interval_sec = int(require(payload, "interval_sec", target="payload.interval_sec"))
    slot = int(require(payload, "slot", target="payload.slot"))

    job_config = ctx.config.worker_jobs[OutboxEventType.SYNC_ALERTS.value]

    batch_size = job_config["batch_size"]
    ttl_sec = job_config["ttl_sec"]
    run_key = job_config["run_key"]

    tmp_prefix = f"{redis_key_prefix}:{TMP}:{run_key}:{slot}:{interval_sec}"

    redis_snapshot_key = f"{redis_key_prefix}:{SNAP}:{run_key}" # 실사용 snapshot 목록
    tmp_snapshot_key = f"{tmp_prefix}:{SNAP}"

    redis_bucket_key = f"{redis_key_prefix}:{BUCKET}:{run_key}" # 실사용 개별 bucket key prefix
    tmp_bucket_key = f"{tmp_prefix}:{BUCKET}"

    redis_bucket_index_key = f"{redis_bucket_key}:{INDEX}" # 실사용 bucket key set 목록
    tmp_bucket_index_key = f"{tmp_bucket_key}:{INDEX}"

    lock_key = f"{redis_key_prefix}:{LOCK}:{run_key}:{slot}:{interval_sec}"
    meta_key = f"{redis_key_prefix}:{META}:{run_key}"

    token = try_acquire_lock(
        ctx.redis_client,
        lock_key,
        ttl_sec=ctx.config.outbox_send_lock_ttl_sec,
    )
    if not token:
        raise SkipHandler("locked")

    total = 0
    offset = 0

    try:
        r = ctx.redis_client.conn()
        old_tmp_bucket_keys = r.smembers(tmp_bucket_index_key)
        old_real_bucket_keys = r.smembers(redis_bucket_index_key)
        all_bucket_keys: set[str] = set()

        pipe = r.pipeline(transaction=False)

        for raw_bucket_key in old_tmp_bucket_keys:
            bucket_key = raw_bucket_key.decode() if isinstance(raw_bucket_key, bytes) else raw_bucket_key
            pipe.delete(f"{tmp_bucket_key}:{bucket_key}")

        pipe.delete(tmp_bucket_index_key)
        pipe.delete(tmp_snapshot_key)

        pipe.execute()

        while True:
            alerts = ctx.svcs.alerts.sync_alerts(
                limit=batch_size,
                offset=offset,
            )
            # print("alerts", alerts)
            if not alerts:
                break

            mapping: dict[str, str] = {}
            bucket_mapping: dict[str, list[str]] = {}

            for row in alerts:
                alert_id = row.get("alert_id")
                if not alert_id:
                    continue

                alert_id_str = str(alert_id)

                # print("alerts row", row)
                mapping[str(alert_id)] = json.dumps(
                    row,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )

                bucket_key = row.get("bucket_key")
                if bucket_key:
                    bucket_mapping.setdefault(str(bucket_key), []).append(alert_id_str)

            # print("alerts mapping", mapping)
            if mapping:
                pipe = r.pipeline(transaction=False)
                pipe.hset(tmp_snapshot_key, mapping=mapping)

                for bucket_key, alert_ids in bucket_mapping.items():
                    pipe.sadd(f"{tmp_bucket_key}:{bucket_key}", *alert_ids)
                    pipe.sadd(tmp_bucket_index_key, bucket_key)
                    all_bucket_keys.add(bucket_key)

                pipe.execute()
                total += len(mapping)

            offset += batch_size

        finished_at = utcnow()
        started_epoch_ms = datetime_to_epoch_ms(started_at)
        finished_epoch_ms = datetime_to_epoch_ms(finished_at)

        # pipe.rename은 redis cluster가 의도적으로 막아둬서 pipeline 안에서 사용 불가하기 때문에 따로 빼서 사용해야함
        if total > 0:
            r.rename(tmp_snapshot_key, redis_snapshot_key)

            for bucket_key in all_bucket_keys:
                r.rename(f"{tmp_bucket_key}:{bucket_key}", f"{redis_bucket_key}:{bucket_key}")
            
            r.rename(tmp_bucket_index_key, redis_bucket_index_key)

            pipe = r.pipeline(transaction=False)

            for raw_bucket_key in old_real_bucket_keys:
                bucket_key = raw_bucket_key.decode() if isinstance(raw_bucket_key, bytes) else raw_bucket_key

                if bucket_key not in all_bucket_keys:
                    pipe.delete(f"{redis_bucket_key}:{bucket_key}")

            pipe.execute()
            
        else:
            # 활성 알림이 0개니까 기존 스냅샷 제거
            pipe = r.pipeline(transaction=False)

            pipe.delete(redis_snapshot_key)

            for raw_bucket_key in old_real_bucket_keys:
                bucket_key = raw_bucket_key.decode() if isinstance(raw_bucket_key, bytes) else raw_bucket_key
                pipe.delete(f"{redis_bucket_key}:{bucket_key}")

            pipe.delete(redis_bucket_index_key)

            pipe.execute()
        
        meta = {
            "run_key": run_key,
            "slot": slot,
            "interval_sec": interval_sec,
            "total": total,
            "started_at_epoch_ms": started_epoch_ms,
            "synced_at_epoch_ms": finished_epoch_ms,
        }

        r.set(
            meta_key,
            json.dumps(
                meta,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )

        # TTL이 필요하면 tmp/meta 둘 다 TTL 적용
        # if ttl_sec > 0:
        #     pipe.expire(tmp_snapshot_key, ttl_sec)
        #     pipe.expire(meta_key, ttl_sec)

        logger.info(
            "sync_alerts: wrote %s alerts into redis_snapshot_key=%s", total, redis_snapshot_key
        )

        return {"count": total, "redis_snapshot_key": redis_snapshot_key, "ttl_sec": ttl_sec}
    except SkipHandler:
        # 스킵 핸들러도 그대로 전달
        raise
    except Exception as e:
        raise FatalHandler(
            "sync_alerts_fatal",
            meta={"error": str(e)},
        ) from e

    finally:
        release_lock(ctx.redis_client, lock_key, token)
