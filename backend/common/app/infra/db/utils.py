from enum import Enum
from sqlalchemy.exc import IntegrityError
from dataclasses import fields, is_dataclass
from typing import Any, Mapping


def to_row_dict(row: Any) -> dict:
    if isinstance(row, Mapping):
        return dict(row)

    if is_dataclass(row):
        return {f.name: getattr(row, f.name) for f in fields(row)}

    raise TypeError(f"Unsupported row type: {type(row)!r}")


def to_db_value(v):
    if v is None:
        return None
    return v.value if isinstance(v, Enum) else str(v).strip()


def is_mysql_duplicate_key(err: IntegrityError) -> bool:
    # pymysql.err.IntegrityError: args[0] == 1062 (Duplicate entry)
    orig = getattr(err, "orig", None)
    args = getattr(orig, "args", ())
    return bool(args) and args[0] == 1062
