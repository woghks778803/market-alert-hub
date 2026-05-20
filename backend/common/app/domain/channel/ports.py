from typing import Protocol
import app.domain.channel.dto as ChannelDTO

class ChannelMessage(Protocol):
    def send_message(
        self,
        *,
        target: str,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> ChannelDTO.ChannelMessageResult:
        raise NotImplementedError

    def send_messages(
        self,
        messages: list[ChannelDTO.ChannelMessage],
    ) -> list[ChannelDTO.ChannelMessageResult]:
        raise NotImplementedError