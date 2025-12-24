import asyncio
import logging
import sys

from app.run import run
from app.wiring import build_runtime, collector_config


def _configure_logging() -> None:
    """
    컨테이너 공통 로깅 초기화.
    - settings.LOG_LEVEL을 그대로 사용 (worker/dispatcher와 동일 철학)
    - 포맷은 단순하게 시작하고, 나중에 필요하면 structured logging으로 확장
    """
    level = getattr(collector_config, "log_level", "INFO")

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    _configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("collector.boot")

    runtime = build_runtime()

    try:
        asyncio.run(run(runtime))
        logger.info("collector.exit")
        return 0

    except KeyboardInterrupt:
        logger.info("collector.interrupted")
        return 0

    except Exception:
        logger.exception("collector.crash")
        return 1

    finally:
        # wiring/build_runtime에서 close 훅을 제공하면 best-effort로 정리
        close = getattr(runtime, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                logger.exception("collector.runtime_close_failed")


if __name__ == "__main__":
    sys.exit(main())
