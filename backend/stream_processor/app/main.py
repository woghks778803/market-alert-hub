import asyncio
import logging
import sentry_sdk
import sys

from app.core.logging import setup_logging, resolve_log_level
from app.core.constants import DeploymentEnvironment
from app.run import run
from app.wiring import build_runtime


def main() -> int:
    rt = build_runtime()
    service_name = rt.ctx.config.service_name

    setup_logging(
        level=resolve_log_level(rt.ctx.config.log_level),
        service=service_name,
    )

    sentry_sdk.init(
        dsn=rt.ctx.config.sentry_dsn,
        environment=rt.ctx.config.deploy_env,
        sample_rate=rt.ctx.config.sample_rate,
        traces_sample_rate=rt.ctx.config.traces_sample_rate,
        # enable_logs=True,
    )
    sentry_sdk.set_tag("service", service_name)
    sentry_sdk.capture_message(f"sentry {service_name} connected")

    logger = logging.getLogger(__name__)
    logger.info(f"{service_name}.boot")

    try:
        asyncio.run(run(rt))
        logger.info(f"{service_name}.exit")
        return 0

    except KeyboardInterrupt:
        logger.info(f"{service_name}.interrupted")
        return 0

    except Exception:
        logger.exception(f"{service_name}.crash")
        return 1

    finally:
        # wiring/build_runtime에서 close 훅을 제공하면 best-effort로 정리
        close = getattr(rt, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                logger.exception(f"{service_name}.runtime_close_failed")


if __name__ == "__main__":
    sys.exit(main())
