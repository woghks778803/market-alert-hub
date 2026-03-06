import logging
import sentry_sdk
import signal
import time

from app.core.logging import setup_logging
from app.core.constants import DeploymentEnvironment
from .wiring import build_dispatcher_runtime

log = logging.getLogger(__name__)


def run() -> None:
    rt = build_dispatcher_runtime()
    if rt.config.deploy_env == DeploymentEnvironment.PROD:
        setup_logging(level=logging.INFO, service="dispatcher")
    else:
        setup_logging(level=logging.DEBUG, service="dispatcher")

    sentry_sdk.init(
        dsn=rt.config.sentry_dsn,
        environment=rt.config.deploy_env,
        sample_rate=rt.config.sample_rate,
        traces_sample_rate=rt.config.traces_sample_rate,
        # enable_logs=True,
    )
    sentry_sdk.set_tag("service", "dispatcher")
    sentry_sdk.capture_message("sentry dispatcher connected")

    stop = {"flag": False}

    def _handle_stop(signum, frame):  # noqa: ARG001
        log.warning("dispatcher stopping by signal=%s", signum)
        stop["flag"] = True

    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    poll_limit = rt.config.outbox_poll_limit
    idle_sleep = rt.config.outbox_idle_sleep

    log.info("dispatcher started (poll_limit=%s idle_sleep=%s)", poll_limit, idle_sleep)

    while not stop["flag"]:
        try:
            n = rt.svcs.outboxs.enqueue_outbox_pending(poll_limit, rt.q_outbox)
            if not n:
                time.sleep(idle_sleep)
                continue
        except Exception:
            log.exception("dispatcher loop error")
            time.sleep(idle_sleep)

    log.info("dispatcher stopped")
