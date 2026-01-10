import json
import logging
import time
from typing import Any, Mapping

from app.runtime.app_context import WorkerContext
from app.util.utils import require, try_acquire_lock, release_lock

log = logging.getLogger(__name__)


def handle_sync_exchanges(
    ctx: WorkerContext, payload: Mapping[str, Any]
) -> dict[str, Any]:
    batch_size = require(payload, "batch_size", target="payload.batch_size")
    ttl_sec = require(payload, "ttl_sec", target="payload.ttl_sec")
    redis_key = require(payload, "redis_key", target="payload.redis_key")

    r = ctx.redis_client.conn()

    tmp_key = f"{redis_key}:tmp:{int(time.time())}"

    total = 0
    offset = 0

    # temp key에 "전체 스냅샷"을 JSON Lines 로 쌓는 방식(간단/안전/대량에도 무난)
    # - consumer가 필요하면 GET + splitlines 해서 파싱 가능
    # - 더 최적화하려면 hash/set 구조로 바꿔도 되지만, 일단 스냅샷은 이게 깔끔함
    pipe = r.pipeline(transaction=False)
    pipe.delete(tmp_key)

    while True:
        exchanges = ctx.svcs.markets.list_exchanges_by_filter(
            limit=batch_size, offset=offset
        )
        if not exchanges:
            break

        for ex in exchanges:
            pipe.rpush(
                tmp_key,
                json.dumps(
                    _exchange_to_payload(ex), ensure_ascii=False, separators=(",", ":")
                ),
            )
        total += len(exchanges)
        offset += len(exchanges)

        # 파이프라인을 너무 크게 잡지 않도록 배치 단위로 flush
        pipe.execute()

    # metadata(선택)
    meta_key = f"{redis_key}:meta"
    now_ms = int(time.time() * 1000)

    pipe = r.pipeline(transaction=False)
    pipe.hset(meta_key, mapping={"updated_at_ms": now_ms, "count": total})

    # TTL이 필요하면 tmp/meta 둘 다 TTL 적용
    if ttl_sec > 0:
        pipe.expire(tmp_key, ttl_sec)
        pipe.expire(meta_key, ttl_sec)

    pipe.execute()

    # 원자적 스왑: tmp_key -> redis_key
    # - rename은 원자적
    # - 기존 redis_key가 있으면 덮어씀
    r.rename(tmp_key, redis_key)

    log.info("sync_exchanges: wrote %s exchanges into redis_key=%s", total, redis_key)

    return {"ok": True, "count": total, "redis_key": redis_key, "ttl_sec": ttl_sec}


def _exchange_to_payload(ex: Any) -> dict[str, Any]:
    """
    DTO/엔티티 형태가 뭐든(duck-typing) Redis에 저장할 최소 필드만 뽑는다.
    - DTO에 to_dict()/model_dump()/asdict 같은 게 있으면 그걸 써도 되는데,
      worker는 '저장 포맷'을 통제하려는 목적이니 여기서 명시적으로 제한하는 편이 안전.
    """
    # 흔히 쓰는 필드명 기준. 너 DTO 필드명에 맞춰 필요하면 조정하면 됨.
    return {
        "id": getattr(ex, "id", None),
        "code": getattr(ex, "code", None),
        "name": getattr(ex, "name", None),
        "is_active": getattr(ex, "is_active", None),
        # 필요하면 더 추가 (예: "created_at", "updated_at", "country", ...)
    }
