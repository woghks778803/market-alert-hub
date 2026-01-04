import asyncio
import logging
import signal
from collections.abc import Iterable
from typing import Callable

logger = logging.getLogger(__name__)


def install_signal_handlers(
    stop_event: asyncio.Event,
    *,
    signals: Iterable[int] = (signal.SIGTERM, signal.SIGINT),
    on_signal: Callable[[int], None] | None = None,
) -> None:
    """
    컨테이너/프로세스 종료 신호(SIGTERM, SIGINT)를 받아서
    collector의 메인 루프에 '정상 종료'를 요청하는 stop_event를 set() 한다.

    - stop_event: run.py에서 while 루프/태스크들이 체크하는 종료 플래그
    - on_signal: 신호 수신 시 추가로 실행할 훅(로깅/메트릭 등). 옵션.
    """
    loop = asyncio.get_running_loop()

    def _handler(sig: int) -> None:
        # 여러 번 신호가 들어올 수 있으니 idempotent 하게 처리
        if not stop_event.is_set():
            logger.info("received signal=%s -> graceful shutdown requested", sig)
            stop_event.set()
        else:
            logger.info("received signal=%s (already stopping)", sig)

        if on_signal is not None:
            try:
                on_signal(sig)
            except Exception:
                logger.exception("on_signal hook failed (sig=%s)", sig)

    for s in signals:
        try:
            # 대부분의 리눅스 컨테이너 환경에서 동작 (ECS/Fargate 등)
            loop.add_signal_handler(s, _handler, s)
        except NotImplementedError:
            # 일부 환경(예: Windows, 특정 런타임)에서는 add_signal_handler 미지원
            # 이 경우 synchronous signal handler로 대체
            signal.signal(s, lambda *_: _handler(s))
