import asyncio
import logging
import sys

from app.core.logging import setup_logging
from app.run import run
from app.wiring import build_runtime


def main() -> int:
    setup_logging(service="collector")
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
