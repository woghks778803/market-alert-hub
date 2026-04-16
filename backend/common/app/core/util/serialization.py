from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

import json

def to_canonical_json(fingerprint_dict: dict | None) -> str | None:
    if not fingerprint_dict:
        return None
    return json.dumps(fingerprint_dict, sort_keys=True, separators=(",", ":"))

def json_safe(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, datetime | date):
        return value.isoformat()

    if isinstance(value, dict):
        return {str(json_safe(k)): json_safe(v) for k, v in value.items()}

    if isinstance(value, list | tuple | set):
        return [json_safe(v) for v in value]

    return value