import logging
import signal
from collections.abc import Iterable
from typing import Callable

logger = logging.getLogger(__name__)


def install_signal_handlers(
    stop_event,
    *,
    signals: Iterable[int] = (signal.SIGTERM, signal.SIGINT),
    on_signal: Callable[[int], None] | None = None,
) -> None:
    """
    컨테이너/프로세스 종료 신호(SIGTERM, SIGINT)를 받아
    scheduler의 루프가 "graceful shutdown"으로 빠질 수 있게 stop_event를 set 한다.

    - stop_event: threading.Event 같은 "set()/is_set()"을 가진 객체를 기대(duck-typing)
    - on_signal: 신호 수신 시 추가 작업(로그/메트릭 등), 옵션
    """

    def _handler(sig: int, _frame=None) -> None:
        # 여러 번 들어와도 idempotent 하게 처리
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
            signal.signal(s, _handler)
        except Exception:
            # 일부 환경/플랫폼에서 제한이 있을 수 있어 최소한의 fallback 제공
            signal.signal(s, lambda sig, frame: _handler(sig, frame))
