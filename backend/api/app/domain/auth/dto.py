from dataclasses import dataclass

@dataclass(slots=True, frozen=True)
class UserToken:
    user_id: int
    access_token: str