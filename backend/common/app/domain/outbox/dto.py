from dataclasses import dataclass, asdict
from datetime import datetime
from app.core.constants import OutboxStatus
from typing import Iterable, Any

@dataclass(frozen=True)
class OutboxMessage:
    message_id: str
    outbox_id: int


@dataclass(slots=True)
class Outbox:
    id: int
    trace_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: int
    payload: dict[str, Any]
    status: OutboxStatus
    attempts: int
    next_run_at: datetime
    created_at: datetime
    updated_at: datetime
    outbox_fingerprint: bytes | None
    last_attempted_at: datetime | None
    sent_at: datetime | None
    final_failed_at: datetime | None


@dataclass(slots=True)
class OutboxAttempt:
    id: int
    outbox_id: int
    attempt_no: int
    success: int
    retryable: int
    started_at: datetime
    result_payload: dict
    result_code: str | None
    result_message: str | None
    finished_at: datetime | None


@dataclass(slots=True)
class OutboxFilter:
    id: int | None = None
    ids: list[int] | None = None
    status: OutboxStatus | None = None
    # trace_id: str | None = None
    # event_type: str | None = None
    # aggregate_type: str | None = None
    # aggregate_id: int | None = None
    # dedupe_key: str | None = None
    # payload: dict | None = None
    # status: OutboxStatus | None = None
    # attempts: int | None = None
    next_run_at: datetime | None = None
    # last_attempted_at: datetime | None = None
    # sent_at: datetime | None = None
    # final_failed_at: datetime | None = None
    # created_at: datetime | None = None
    # updated_at: datetime | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        # None 제거 + ids는 list로 강제
        if d["ids"] is not None and not isinstance(d["ids"], list):
            d["ids"] = list(d["ids"])
        return {k: v for k, v in d.items() if v is not None}


@dataclass(slots=True)
class OutboxUpdate:
    status: OutboxStatus | None = None
    attempts: int | None = None
    next_run_at: datetime | None = None
    sent_at: datetime | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass(slots=True)
class OutboxCreate:
    trace_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: int
    payload: dict[str, Any]
    status: OutboxStatus
    attempts: int
    next_run_at: datetime | None = None
    outbox_fingerprint: bytes | None = None


@dataclass(slots=True)
class OutboxAttemptCreate:
    outbox_id: int
    attempt_no: int
    success: int
    retryable: int
    started_at: datetime
    result_payload: dict[str, Any]
    result_code: str | None = None
    result_message: str | None = None
    finished_at: datetime | None = None
