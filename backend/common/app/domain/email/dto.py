from dataclasses import dataclass, asdict
from datetime import datetime
from app.core.constants import EmailVerificationStatus

@dataclass(slots=True)
class EmailVerificationFilter:
    id: int | None = None
    user_id: int | None = None
    statuses: tuple[EmailVerificationStatus, ...] | None = None

    # 시간 조건(필요할 때만)
    expires_after: datetime | None = None   # expires_at > expires_after
    expires_before: datetime | None = None  # expires_at < expires_before


    def to_dict(self) -> dict:
        d = asdict(self)
        # None 제거 + ids는 list로 강제
        if d["ids"] is not None and not isinstance(d["ids"], list):
            d["ids"] = list(d["ids"])
        return {k: v for k, v in d.items() if v is not None}

@dataclass(slots=True)
class EmailVerificationUpdate:
    status: EmailVerificationStatus | None = None
    expires_at: datetime | None = None
    sent_at: datetime | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}