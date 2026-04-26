from dataclasses import dataclass

from app.domain import AuthPort, AuthDTO
from app.infra.external.oauth.kakao.rest_client import KakaoRestClient


@dataclass
class KakaoOAuth(AuthPort.KakaoOAuth):
    rest_client: KakaoRestClient

    # -------------------------
    # 인가 URL 생성
    # -------------------------
    def build_authorize_path(self, state: str) -> str:
        return self.rest_client.build_authorize_path(state)

    # -------------------------
    # code → identity 반환
    # -------------------------
    def fetch_identity(self, code: str) -> AuthDTO.OAuthIdentity:
        token_data = self.rest_client.exchange_code(code)

        access_token: str = token_data["access_token"]

        user_data = self.rest_client.get_user_info(access_token)

        return self._to_identity(user_data)

    # -------------------------
    # 연결 해제
    # -------------------------
    def unlink(self, provider_user_id: int) -> None:
        self.rest_client.unlink(provider_user_id)

    # -------------------------
    # 내부 변환 로직
    # -------------------------
    @staticmethod
    def _to_identity(user_data: dict) -> AuthDTO.OAuthIdentity:
        kakao_account: dict | None = user_data.get("kakao_account")
        profile: dict | None = kakao_account.get("profile") if kakao_account else None

        return AuthDTO.OAuthIdentity(
            provider_user_id=str(user_data["id"]),
            email=kakao_account.get("email") if kakao_account else None,
            nickname=profile.get("nickname") if profile else None,
        )
