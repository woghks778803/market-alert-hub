from dataclasses import dataclass

from app.domain import ChannelPort, ChannelDTO
from app.infra.external.notify.fcm.rest_client import (
    FcmRestClient,
    FcmSendMessage,
    FcmSendResult,
)


@dataclass
class FcmPush(ChannelPort.ChannelMessage):
    rest_client: FcmRestClient

    def send_message(
        self,
        *,
        target: str,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> ChannelDTO.ChannelMessageResult:
        result = self.rest_client.send_message(
            token=target,
            title=title,
            body=body,
            data=data,
        )

        return self._to_channel_message_result(result)

    def send_messages(
        self,
        messages: list[ChannelDTO.ChannelMessage],
    ) -> list[ChannelDTO.ChannelMessageResult]:
        results = self.rest_client.send_messages(
            [
                FcmSendMessage(
                    token=item.target,
                    title=item.title,
                    body=item.body,
                    data=item.data,
                )
                for item in messages
            ]
        )

        return [
            self._to_channel_message_result(result)
            for result in results
        ]

    @staticmethod
    def _to_channel_message_result(
        result: FcmSendResult,
    ) -> ChannelDTO.ChannelMessageResult:
        return ChannelDTO.ChannelMessageResult(
            success=result.success,
            message_id=result.message_id,
            error=result.error,
        )