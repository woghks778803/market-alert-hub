import asyncio
import logging
import signal

import sentry_sdk

from app.core.constants import DeploymentEnvironment
from app.core.logging import setup_logging
from .wiring import build_dispatcher_runtime

log = logging.getLogger(__name__)


async def run() -> None:
    rt = build_dispatcher_runtime()
    service_name = rt.config.service_name

    if rt.config.deploy_env == DeploymentEnvironment.PROD:
        setup_logging(level=logging.INFO, service=service_name)
    else:
        setup_logging(level=logging.DEBUG, service=service_name)

    sentry_sdk.init(
        dsn=rt.config.sentry_dsn,
        environment=rt.config.deploy_env,
        sample_rate=rt.config.sample_rate,
        traces_sample_rate=rt.config.traces_sample_rate,
    )
    sentry_sdk.set_tag("service", service_name)
    sentry_sdk.capture_message(f"sentry {service_name} connected")

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def handle_stop() -> None:
        log.warning(f"{service_name} stopping")
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, handle_stop)

    poll_limit = rt.config.outbox_poll_limit
    idle_sleep = rt.config.outbox_idle_sleep

    while not stop_event.is_set():
        try:
            count = await rt.svcs.outboxs.enqueue_outbox_pending(poll_limit)

            if not count:
                try:
                    await asyncio.wait_for(
                        stop_event.wait(),
                        timeout=idle_sleep,
                    )
                except TimeoutError:
                    pass

        except Exception:
            log.exception(f"{service_name} loop error")

            try:
                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=idle_sleep,
                )
            except TimeoutError:
                pass