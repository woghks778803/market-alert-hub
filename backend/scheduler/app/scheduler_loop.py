import time


def run_scheduler_loop(stop_event, ctx, tasks):
    """
    1초 tick 루프.
    - 매초 tasks를 돌며 "slot이 바뀌었는지" 확인하고,
      바뀌었으면 해당 task가 outbox 1건(또는 몇 건) 생성.
    - task 내부에서 outbox_fingerprint 유니크로 중복은 DB가 막는다.
    """
    # wall-clock 1초 정렬(가능한 한 초 경계에 맞춤)
    next_tick = int(time.time()) + 1

    while not stop_event.is_set():
        now = time.time()
        sleep_sec = next_tick - now
        if sleep_sec > 0:
            stop_event.wait(timeout=sleep_sec)
            if stop_event.is_set():
                break

        now_epoch = int(time.time())

        for task in tasks:
            try:
                task.tick(now_epoch, ctx)
            except Exception:
                # 여기서 죽이거나(=supervisor 재시작) 삼키거나 정책 선택.
                # 초기엔 로깅만 하고 계속 가는 게 보통 편하다.
                _log_exception(
                    f"scheduler.task_failed name={getattr(task, 'name', 'unknown')}"
                )

        next_tick += 1


def _log_exception(msg):
    import traceback

    print(f"{msg}\n{traceback.format_exc()}", flush=True)
