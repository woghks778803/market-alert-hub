from dataclasses import dataclass

import firebase_admin
from firebase_admin import credentials, messaging


@dataclass(frozen=True)
class FcmRestClientConfig:
    service_account_path: str
    project_id: str
    app_name: str = "mah-fcm"


@dataclass(frozen=True)
class FcmSendMessage:
    token: str
    title: str
    body: str
    data: dict[str, str] | None = None


@dataclass(frozen=True)
class FcmSendResult:
    success: bool
    message_id: str | None = None
    error: str | None = None


class FcmRestClient:
    def __init__(self, config: FcmRestClientConfig) -> None:
        if not config.service_account_path:
            raise RuntimeError("FCM service_account_path is required")

        if not config.project_id:
            raise RuntimeError("FCM project_id is required")

        self._config = config
        self._app = self._init_app(config)

    def send_message(
        self,
        *,
        token: str,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> FcmSendResult:
        results = self.send_messages(
            [
                FcmSendMessage(
                    token=token,
                    title=title,
                    body=body,
                    data=data,
                )
            ]
        )

        return results[0]

    def send_messages(
        self,
        messages: list[FcmSendMessage],
    ) -> list[FcmSendResult]:
        if not messages:
            return []

        if len(messages) > 500:
            raise RuntimeError("FCM send_each messages must not exceed 500")

        fcm_messages = [
            messaging.Message(
                token=item.token,
                data={
                    **(item.data or {}),
                    "title": item.title,
                    "body": item.body,
                },
                android=messaging.AndroidConfig(
                    priority="high",
                ),
            )
            for item in messages
        ]

        response = messaging.send_each(
            fcm_messages,
            app=self._app,
        )

        return [
            self._to_result(send_response)
            for send_response in response.responses
        ]

    def _init_app(self, config: FcmRestClientConfig) -> firebase_admin.App:
        try:
            return firebase_admin.get_app(config.app_name)
        except ValueError:
            cred = credentials.Certificate(config.service_account_path)

            return firebase_admin.initialize_app(
                cred,
                {
                    "projectId": config.project_id,
                },
                name=config.app_name,
            )

    @staticmethod
    def _to_result(send_response: messaging.SendResponse) -> FcmSendResult:
        if send_response.success:
            return FcmSendResult(
                success=True,
                message_id=send_response.message_id,
            )

        return FcmSendResult(
            success=False,
            error=str(send_response.exception),
        )


def get_fcm_rest_client(
    config: FcmRestClientConfig,
) -> FcmRestClient:
    return FcmRestClient(config)