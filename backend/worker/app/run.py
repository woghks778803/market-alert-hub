import logging
import sentry_sdk
import signal
from rq import Worker

from app.core.logging import setup_logging
from app.core.constants import DeploymentEnvironment
from .wiring import build_worker_runtime

log = logging.getLogger(__name__)


def run() -> None:
    rt = build_worker_runtime()
    if rt.config.deploy_env == DeploymentEnvironment.PROD:
        setup_logging(level=logging.INFO, service="worker")
    else:
        setup_logging(level=logging.DEBUG, service="worker")

    sentry_sdk.init(
        dsn=rt.config.sentry_dsn,
        environment=rt.config.deploy_env,
        sample_rate=rt.config.sample_rate,
        traces_sample_rate=rt.config.traces_sample_rate,
        # enable_logs=True,
    )
    sentry_sdk.set_tag("service", "worker")
    sentry_sdk.capture_message("sentry worker connected")

    worker = Worker([rt.q_outbox], connection=rt.redis_conn)

    # SIGTERM 받으면 현재 job 끝내고 종료
    def _handle_stop(signum, frame):  # noqa: ARG001
        log.warning("worker stopping by signal=%s", signum)
        try:
            worker.request_stop(signum=signum, frame=frame)
        except Exception:
            log.exception("failed to request_stop")

    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    worker.work(with_scheduler=True)
