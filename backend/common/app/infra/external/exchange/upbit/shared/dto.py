from dataclasses import dataclass
from typing import Literal, Any


# ---------- REST ----------


@dataclass(frozen=True)
class UpbitMarket:
    market: str
    korean_name: str
    english_name: str


# ---------- WS ----------

UpbitWsChannel = Literal["candle.1s", "ticker", "trade", "orderbook"]


@dataclass(frozen=True)
class UpbitWsSubscribe:
    channel: UpbitWsChannel
    codes: list[str]
    is_only_snapshot: bool = False
    is_only_realtime: bool = False

    def to_frames(self) -> list[dict[str, Any]]:
        """
        Upbit WS는 보통 여러 JSON 오브젝트를 배열로 보내는 형태를 씀(티켓/구독).
        정확한 포맷은 ws_client에서 최종 조립해도 되지만, 일단 스켈레톤 제공.
        """
        return [
            # {"ticket": "..."} 는 ws_client에서 붙이기 쉬움
            {
                "type": self.channel,
                "codes": self.codes,
                "is_only_snapshot": self.is_only_snapshot,
                "is_only_realtime": self.is_only_realtime,
            },
        ]
