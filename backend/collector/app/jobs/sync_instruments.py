import asyncio
import logging
import time
from collections.abc import Awaitable, Callable

from app.internal.state.checkpoint_store import CheckpointStore

log = logging.getLogger(__name__)

SyncOnce = Callable[[], Awaitable[None]]


async def _sleep_or_stop(stop_event: asyncio.Event, seconds: float) -> None:
    """
    seconds 동안 대기하되, stop_event가 먼저 set 되면 즉시 반환.
    """
    if seconds <= 0:
        return
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=seconds)
    except asyncio.TimeoutError:
        return


async def run_sync_instruments_loop(
    *,
    stop_event: asyncio.Event,
    checkpoint_store: CheckpointStore,
    interval_sec: int,
    sync_once: SyncOnce,
    checkpoint_key: str = "collector:catalog_sync",
    on_error_sleep_sec: int = 10,
) -> None:
    """
    1단계: 마켓/심볼 카탈로그 동기화 루프.

    - stop_event: 정상 종료를 위한 플래그(SIGTERM/SIGINT에서 set)
    - checkpoint_store: 마지막 실행 시각/결과 저장(운영 안정성)
    - interval_sec: 성공/실패 여부와 무관하게 루프 기본 주기
    - sync_once: 실제 동기화 1회를 수행하는 콜백(거래소 호출 + DB upsert)
    - checkpoint_key: 저장 키(서비스/환경 별로 구분 가능)
    - on_error_sleep_sec: 실패 시 너무 빠른 재시도 폭주 방지용 짧은 대기

    주의:
    - 이 파일은 “루프/운영”만 담당하고,
      어떤 거래소를 호출하고 DB에 어떻게 upsert 하는지는 sync_once에 위임한다.
    """
    if interval_sec <= 0:
        raise ValueError("interval_sec must be > 0")

    log.info(
        "catalog_sync.loop.start interval_sec=%s checkpoint_key=%s",
        interval_sec,
        checkpoint_key,
    )

    while not stop_event.is_set():
        started_at = time.time()

        try:
            await sync_once()

            # 성공 체크포인트 기록(최소한의 운영 가시성)
            await checkpoint_store.set(
                checkpoint_key,
                {
                    "last_success_epoch": int(time.time()),
                    "last_error": None,
                },
            )
            log.info("catalog_sync.once.ok")

        except asyncio.CancelledError:
            raise

        except Exception as e:
            # 실패 체크포인트 기록 + 로깅
            await checkpoint_store.set(
                checkpoint_key,
                {
                    "last_error_epoch": int(time.time()),
                    "last_error": f"{e.__class__.__name__}: {e}",
                },
            )
            log.exception("catalog_sync.once.fail")

            # 실패 직후 너무 빠른 루프 반복을 막기 위한 짧은 대기
            await _sleep_or_stop(stop_event, on_error_sleep_sec)

        # 다음 주기까지 대기(실행 시간만큼 차감)
        elapsed = time.time() - started_at
        sleep_sec = max(0.0, float(interval_sec) - float(elapsed))
        await _sleep_or_stop(stop_event, sleep_sec)

    log.info("catalog_sync.loop.stop")
