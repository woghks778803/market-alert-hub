from dataclasses import dataclass
from typing import Literal, Any


# ---------- REST ----------


@dataclass(frozen=True)
class UpbitMarket:
    market: str  # e.g. "KRW-BTC"
    korean_name: str
    english_name: str


# ---------- WS ----------

# Upbit WS에서 흔히 등장하는 타입(정확한 스펙은 거래소별로 다름)
UpbitWsChannel = Literal["ticker", "trade", "orderbook"]


@dataclass(frozen=True)
class UpbitWsSubscribe:
    channel: UpbitWsChannel
    codes: list[str]  # e.g. ["KRW-BTC", "KRW-ETH"]
    is_only_realtime: bool = True  # 필요 시 옵션으로 노출

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
                "isOnlyRealtime": self.is_only_realtime,
            },
        ]
