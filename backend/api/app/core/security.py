import time, jwt
from datetime import datetime, timedelta
from typing import Tuple


SECRET = "change-me"


def issue_tokens(
    user_id: int, access_minutes: int = 10, refresh_days: int = 14
) -> Tuple[str, str]:
    now = datetime.utcnow()
    access = jwt.encode(
        {"sub": user_id, "exp": now + timedelta(minutes=access_minutes)},
        SECRET,
        algorithm="HS256",
    )
    refresh = jwt.encode(
        {"sub": user_id, "exp": now + timedelta(days=refresh_days)},
        SECRET,
        algorithm="HS256",
    )
    return access, refresh
