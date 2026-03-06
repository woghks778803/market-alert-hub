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
        setup_logging(level=logging.INFO, service="scheduler")
    else:
        setup_logging(level=logging.DEBUG, service="scheduler")

    sentry_sdk.init(
        dsn=rt.ctx.config.sentry_dsn,
        environment=rt.ctx.config.deploy_env,
        traces_sample_rate=0,
        # enable_logs=True,
    )
    sentry_sdk.set_tag("service", "scheduler")
    sentry_sdk.capture_message("sentry scheduler connected")

    logger = logging.getLogger(__name__)
    logger.info("scheduler.boot")

    try:
        run(rt)  # 동기식 실행
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
        close = getattr(rt, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                logger.exception("scheduler.runtime_close_failed")


if __name__ == "__main__":
    sys.exit(main())
