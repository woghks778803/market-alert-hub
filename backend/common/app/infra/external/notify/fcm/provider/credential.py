from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2 import service_account


@dataclass(frozen=True)
class FcmCredentialConfig:
    service_account_path: str
    scope: str


class FcmAccessToken:
    def __init__(self, config: FcmCredentialConfig) -> None:
        self._config = config
        self._credentials = service_account.Credentials.from_service_account_file(
            config.service_account_path,
            scopes=[config.scope],
        )

    def get_access_token(self) -> str:
        if self._should_refresh():
            self._credentials.refresh(Request())

        if not self._credentials.token:
            raise RuntimeError("FCM access token is empty")

        return self._credentials.token

    def _should_refresh(self) -> bool:
        if not self._credentials.valid:
            return True

        if not self._credentials.expiry:
            return True

        now = datetime.now(timezone.utc)
        expiry = self._credentials.expiry

        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)

        return expiry <= now + timedelta(minutes=5)