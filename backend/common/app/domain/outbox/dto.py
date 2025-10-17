from dataclasses import dataclass, asdict
from datetime import datetime
from app.core.constants import OutboxStatus
from typing import Optional, Iterable

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
    # next_run_at: datetime | None = None
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

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}