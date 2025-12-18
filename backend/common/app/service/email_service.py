from typing import Sequence, Callable
from email_validator import validate_email, EmailNotValidError
from app.domain import UserDTO, EmailDTO, EmailPort, ValidationAppError, CryptoPort
from app.core import dto as CoreDTO
import base64


class EmailService:
    def __init__(
        self,
        client: Callable[[], EmailPort.EmailClient],
        renderer: Callable[[], EmailPort.EmailTemplateRenderer],
        secrets: CryptoPort.SecretCrypto,
        config: CoreDTO.ConfigBag,
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
    #         subject="[PricePing] 회원가입을 환영합니다",
    #         html_body=html,
    #         to=to,
    #     )

    def send_verify(
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
            f"{self._config.public_web_base_url}/auth/verify-email?token={verify_token}"
        )

        html = self.renderer().render(
            "user_email_verify.html",
            {
                "user_name": user.nickname,
                "verify_link": verify_link,
                "expiration_hours": self._config.access_token_minutes,
            },
        )

        return self.client().send(
            subject="[PricePing] 회원가입을 환영합니다",
            html_body=html,
            to=to,
        )

    # def send_alert(
    #     self,
    #     to: Sequence[str],
    #     user_name: str,
    #     exchange: str,
    #     symbol: str,
    #     condition: str,
    #     current_price: str,
    #     currency: str,
    #     settings_link: str,
    #     alert_link: str | None = None,
    # ) -> dict:
    #     to = self._validate_recipients(to)
    #     html = self.renderer().render(
    #         "alert_notification.html",
    #         {
    #             "user_name": user_name,
    #             "exchange": exchange,
    #             "symbol": symbol,
    #             "condition": condition,
    #             "current_price": current_price,
    #             "currency": currency,
    #             "alert_link": alert_link,
    #             "settings_link": settings_link,
    #         },
    #     )
    #     return self.client().send(
    #         subject=f"[알림] {symbol} 목표가 도달",
    #         html_body=html,
    #         to=to,
    #     )
