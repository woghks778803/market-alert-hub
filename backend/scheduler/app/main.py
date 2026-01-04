import logging
import sys

from app.core.logging import setup_logging
from app.run import run
from app.wiring import build_runtime


def main() -> int:
    setup_logging(service="scheduler")
    logger = logging.getLogger(__name__)
    logger.info("scheduler.boot")

    runtime = build_runtime()

    try:
        run(runtime)  # 동기식 실행
        logger.info("scheduler.exit")
        return 0

    except KeyboardInterrupt:
        logger.info("scheduler.interrupted")
        return 0

    except Exception:
        logger.exception("scheduler.crash")
        return 1

    finally:
        # wiring/build_runtime에서 close 훅 제공하면 best-effort로 정리
        close = getattr(runtime, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                logger.exception("scheduler.runtime_close_failed")


if __name__ == "__main__":
    sys.exit(main())
