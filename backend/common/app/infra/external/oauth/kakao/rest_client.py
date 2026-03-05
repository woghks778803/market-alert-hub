from dataclasses import dataclass
from typing import Any, Dict
from urllib.parse import urlencode

from app.infra.external.transport.port.http import SyncHttpTransport, HttpResponse


@dataclass
class KakaoRestClientConfig:
    client_id: str
    redirect_uri: str
    client_secret: str | None = None
    admin_key: str | None = None


class KakaoRestClient:

    def __init__(
        self,
        config: KakaoRestClientConfig,
        *,
        auth_transport: SyncHttpTransport,
        api_transport: SyncHttpTransport,
    ) -> None:
        self._config = config
        self._auth = auth_transport
        self._api = api_transport

    # -------------------------
    # 인가 URL 생성 (HTTP 호출 아님)
    # -------------------------
    def build_authorize_path(self, state: str) -> str:
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self._config.client_id,
                "redirect_uri": self._config.redirect_uri,
                "state": state,
                # "prompt": "login",
            }
        )
        # transport base_url은 bootstrap에서 이미 세팅됨
        return f"/oauth/authorize?{query}"

    # -------------------------
    # code → token 교환
    # -------------------------
    def exchange_code(self, code: str) -> Dict[str, Any]:
        payload = {
            "grant_type": "authorization_code",
            "client_id": self._config.client_id,
            "redirect_uri": self._config.redirect_uri,
            "code": code,
        }

        if self._config.client_secret:
            payload["client_secret"] = self._config.client_secret

        response: HttpResponse = self._auth.post(
            path="/oauth/token",
            data=payload,
        )

        self._raise_if_error(response)
        return response.json()

    # -------------------------
    # 사용자 정보 조회
    # -------------------------
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        response: HttpResponse = self._api.get(
            path="/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        self._raise_if_error(response)
        return response.json()

    # -------------------------
    # 연결 해제
    # -------------------------
    def unlink(self, provider_user_id: int) -> Dict[str, Any]:
        if not self._config.admin_key:
            raise ValueError("admin_key is required for unlink")

        response: HttpResponse = self._api.post(
            path="/v1/user/unlink",
            headers={"Authorization": f"KakaoAK {self._config.admin_key}"},
            data={
                "target_id_type": "user_id",
                "target_id": provider_user_id,
            },
        )

        self._raise_if_error(response)
        return response.json()

    def _raise_if_error(self, response: HttpResponse) -> None:
        if response.status_code >= 400:
            raise RuntimeError(
                f"Kakao API error: {response.status_code} - {response.text}"
            )


def get_kakao_rest_client(
    config: KakaoRestClientConfig,
    auth_transport: SyncHttpTransport,
    api_transport: SyncHttpTransport,
) -> KakaoRestClient:
    return KakaoRestClient(
        config, auth_transport=auth_transport, api_transport=api_transport
    )
