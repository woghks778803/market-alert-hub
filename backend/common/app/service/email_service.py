from typing import Sequence, Callable
from email_validator import validate_email, EmailNotValidError

from app.core import dto as CoreDTO
from app.domain.shared.errors import ValidationAppError
from app.domain import UserDTO, EmailPort, CryptoPort


class EmailService:
    def __init__(
        self,
        client: Callable[[], EmailPort.EmailClient],
        renderer: Callable[[], EmailPort.EmailTemplateRenderer],
        secrets: CryptoPort.SecretCrypto,
        config: CoreDTO.ServiceConfigBag,
    ) -> None:
        self.client = client
        self.renderer = renderer
        self._secrets = secrets
        self._config = config

    def _validate_recipients(self, emails: Sequence[str]) -> list[str]:
        out: list[str] = []
        for e in emails:
            try:
                out.append(validate_email(e, check_deliverability=False).email)
            except EmailNotValidError as ex:
                # 필요시 도메인 예외로 승격 가능
                raise ValidationAppError(f"Invalid email: {e}") from ex
        return out

    # def send_welcome(
    #     self, to: Sequence[str], user_name: str, dashboard_link: str
    # ) -> str:
    #     to = self._validate_recipients(to)

    #     html = self.renderer().render(
    #         "user_welcome.html",
    #         {"user_name": user_name, "dashboard_link": dashboard_link},
    #     )
    #     return self.client().send(
    #         subject="[AlertPing] 회원가입을 환영합니다",
    #         html_body=html,
    #         to=to,
    #     )

    def send_email_verify(
        self, *, user: UserDTO.UserEmailInfo, verify_token: str
    ) -> dict:

        if user.email_ciphertext is None or user.email_nonce is None:
            raise ValidationAppError("user email is not set", target="user.email")

        to = self._secrets.decrypt(
            ciphertext=user.email_ciphertext,
            nonce=user.email_nonce,
        )  # 복호화 검증용 호출

        to = self._validate_recipients([to.decode("utf-8")])

        verify_link = (
            f"{self._config.public_api_base_url}/auth/verify-email?token={verify_token}"
        )
        html = self.renderer().render(
            "user_email_verify.html",
            {
                "user_name": user.nickname,
                "verify_link": verify_link,
                "expiration_hours": self._config.email_token_minutes,
            },
        )

        return self.client().send(
            subject="[AlertPing] 회원가입을 환영합니다",
            html_body=html,
            to=to,
        )

    def send_password_reset(
        self, *, user: UserDTO.UserEmailInfo, verify_token: str
    ) -> dict:

        if user.email_ciphertext is None or user.email_nonce is None:
            raise ValidationAppError("user email is not set", target="user.email")

        to = self._secrets.decrypt(
            ciphertext=user.email_ciphertext,
            nonce=user.email_nonce,
        )

        to = self._validate_recipients([to.decode("utf-8")])

        verify_link = f"{self._config.public_web_base_url}/auth/reset-password?token={verify_token}"

        html = self.renderer().render(
            "user_password_reset.html",
            {
                "user_name": user.nickname,
                "verify_link": verify_link,
                "expiration_hours": self._config.email_token_minutes,
            },
        )

        return self.client().send(
            subject="[AlertPing] 비밀번호 재설정 안내드립니다",
            html_body=html,
            to=to,
        )
