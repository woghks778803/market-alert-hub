import json

def to_canonical_json(fingerprint_dict: dict | None) -> str | None:
    if not fingerprint_dict:
        return None
    return json.dumps(fingerprint_dict, sort_keys=True, separators=(",", ":"))