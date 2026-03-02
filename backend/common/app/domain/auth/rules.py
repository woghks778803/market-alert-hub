import secrets
import string


def generate_default_nickname() -> str:
    alphabet = string.ascii_lowercase + string.digits
    suffix = "".join(secrets.choice(alphabet) for _ in range(8))
    return f"user_{suffix}"
