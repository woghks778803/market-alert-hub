import asyncio
import logging
import sentry_sdk
import sys

from app.core.logging import setup_logging
from app.core.constants import DeploymentEnvironment
from app.run import run
from app.wiring import build_runtime


def main() -> int:
    rt = build_runtime()
    if rt.ctx.config.deploy_env == DeploymentEnvironment.PROD:
        setup_logging(level=logging.INFO, service="collector")
    else:
        setup_logging(level=logging.DEBUG, service="collector")

    sentry_sdk.init(
        dsn=rt.ctx.config.sentry_dsn,
        environment=rt.ctx.config.deploy_env,
        sample_rate=rt.ctx.config.sample_rate,
        traces_sample_rate=rt.ctx.config.traces_sample_rate,
        # enable_logs=True,
    )
    sentry_sdk.set_tag("service", "collector")
    sentry_sdk.capture_message("sentry collector connected")

    logger = logging.getLogger(__name__)
    logger.info("collector.boot")

    try:
        asyncio.run(run(rt))
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
        close = getattr(rt, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                logger.exception("collector.runtime_close_failed")


if __name__ == "__main__":
    sys.exit(main())
