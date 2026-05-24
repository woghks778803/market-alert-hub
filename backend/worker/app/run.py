import logging
import time
import signal
import socket

import sentry_sdk

from app.core.constants import DeploymentEnvironment, StreamType
from app.core.logging import setup_logging, resolve_log_level
from app.tasks import deliver_outbox_event
from .wiring import build_worker_runtime

log = logging.getLogger(__name__)


def run() -> None:
    rt = build_worker_runtime()
    service_name = rt.config.service_name

    setup_logging(
        level=resolve_log_level(rt.config.log_level),
        service=service_name,
    )

    sentry_sdk.init(
        dsn=rt.config.sentry_dsn,
        environment=rt.config.deploy_env,
        sample_rate=rt.config.sample_rate,
        traces_sample_rate=rt.config.traces_sample_rate,
    )
    sentry_sdk.set_tag("service", service_name)
    sentry_sdk.capture_message(f"sentry {service_name} connected")

    stop = {"flag": False}

    def _handle_stop(signum, frame):  # noqa: ARG001
        log.warning(f"{service_name} stopping by signal=%s", signum)
        stop["flag"] = True

    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    
    consumer_name = f"{service_name}:{StreamType.PERSIST_OUTBOX_EVENTS.value}:{socket.gethostname()}"
    batch_size = rt.config.outbox_event_batch_size
    block_ms = rt.config.outbox_event_block_ms

    rt.svcs.outbox_event.ensure_persist_group()

    log.info(
        f"{service_name} started (consumer=%s batch_size=%s block_ms=%s)",
        consumer_name,
        batch_size,
        block_ms,
    )

    while not stop["flag"]:
        try:
            # 오래된 pending부터 회수
            messages = rt.svcs.outbox_event.claim_persist_outbox_events(
                consumer_name=consumer_name,
                min_idle_time_ms=30_000,
                count=batch_size,
            )

            if messages:
                log.warning(
                    "claimed pending outbox events count=%s message_ids=%s",
                    len(messages),
                    [message.message_id for message in messages],
                )
            else:
                messages = rt.svcs.outbox_event.read_persist_outbox_events(
                    consumer_name=consumer_name,
                    count=batch_size,
                    block_ms=block_ms,
                )

            if not messages:
                continue

            ack_message_ids: list[str] = []
            for message in messages:
                try:
                    deliver_outbox_event(message.outbox_id)
                except Exception:
                    log.exception(
                        "outbox delivery failed outbox_id=%s message_id=%s",
                        message.outbox_id,
                        message.message_id,
                    )
                    continue

                ack_message_ids.append(message.message_id)

            if ack_message_ids:
                ack_count = rt.svcs.outbox_event.ack_persist_outbox_events(
                    message_ids=ack_message_ids,
                )

                log.debug(
                    "acked outbox events requested=%s acknowledged=%s",
                    len(ack_message_ids),
                    ack_count,
                )

                if ack_count != len(ack_message_ids):
                    log.warning(
                        "outbox ack count mismatch requested=%s acknowledged=%s",
                        len(ack_message_ids),
                        ack_count,
                    )

        except Exception:
            log.exception("%s loop error", service_name)
            time.sleep(1)

    log.info("%s stopped", service_name)