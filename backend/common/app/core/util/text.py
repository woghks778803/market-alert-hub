def normalize_spaces(value: str) -> str:
    return " ".join(value.strip().split())


def normalize_nullable_text(value: str | None) -> str | None:
    if not value:
        return None

    normalized = normalize_spaces(value)
    return normalized or None