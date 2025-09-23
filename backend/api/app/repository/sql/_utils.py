from enum import Enum
def to_db_value(v):
    if v is None: return None
    return v.value if isinstance(v, Enum) else str(v).strip()