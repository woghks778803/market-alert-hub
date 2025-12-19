from datetime import datetime, timezone

ISO_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"  # API는 항상 UTC(Z)로

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None :
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt

def parse_iso_utc(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1]
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(s).astimezone(timezone.utc)
