from datetime import datetime, timezone, timedelta

ISO_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"  # API는 항상 UTC(Z)로


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def epoch_to_datetime(epoch: int) -> datetime:
    return datetime.fromtimestamp(int(epoch), tz=timezone.utc)


def datetime_to_epoch_ms(dt: datetime) -> int:
    dt = ensure_utc(dt)
    return int(dt.timestamp() * 1000)


def datetime_to_epoch_sec(dt: datetime) -> int:
    dt = ensure_utc(dt)
    return int(dt.timestamp())


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def parse_iso_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(value)

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def get_milliseconds_ago(dt: datetime, milliseconds: int) -> datetime:
    return dt - timedelta(milliseconds=milliseconds)


def get_days_ago(dt: datetime, days: int) -> datetime:
    return dt - timedelta(days=days)


def get_days_later(dt: datetime, days: int) -> datetime:
    return dt + timedelta(days=days)


def start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)
