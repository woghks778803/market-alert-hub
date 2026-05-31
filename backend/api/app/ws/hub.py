import asyncio
from collections import defaultdict
from typing import Dict, Set
from fastapi import WebSocket

from app.ws.protocols import WsChannelType

class Hub:
    def __init__(self) -> None:
        self._connections: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

        self._single_subscriptions: Dict[
            str,              # conn_id
            Dict[str, str],   # channel_type -> channel
        ] = defaultdict(dict)
        # 특정 채널을 어느 연결에 broadcast할지 조회
        self._single_channel_subscriptions: Dict[str, Set[str]] = defaultdict(set) # channel -> conn_ids

        self._list_subscriptions: Dict[
            str,
            Dict[str, Set[str]],
        ] = defaultdict(dict)
        self._list_channel_subscriptions: Dict[
            tuple[str, str],
            Set[str],
        ] = defaultdict(set)

    async def register(self, conn_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._connections[conn_id] = ws
            # print("_connections", self._connections, len(self._connections))

    async def unregister(self, conn_id: str) -> None:
        async with self._lock:
            self._connections.pop(conn_id, None)

            # 단일 구독 정리
            single_subscriptions = self._single_subscriptions.pop(conn_id, {})

            for channel in single_subscriptions.values():
                conn_ids = self._single_channel_subscriptions.get(channel)

                if conn_ids is None:
                    continue

                conn_ids.discard(conn_id)

                if not conn_ids:
                    self._single_channel_subscriptions.pop(channel, None)

            # 목록 구독 정리
            list_subscriptions = self._list_subscriptions.pop(conn_id, {})

            for channel_type, channels in list_subscriptions.items():
                for channel in channels:
                    key = (channel_type, channel)
                    conn_ids = self._list_channel_subscriptions.get(key)

                    if conn_ids is None:
                        continue

                    conn_ids.discard(conn_id)

                    if not conn_ids:
                        self._list_channel_subscriptions.pop(key, None)

    async def subscribe_list(
        self,
        conn_id: str,
        channel_type: str,
        channels: set[str],
    ) -> None:
        async with self._lock:
            subscriptions = self._list_subscriptions[conn_id]
            current = subscriptions.get(channel_type, set())

            added = channels - current
            removed = current - channels

            for channel in removed:
                key = (channel_type, channel)
                conn_ids = self._list_channel_subscriptions.get(key)

                if conn_ids is None:
                    continue

                conn_ids.discard(conn_id)

                if not conn_ids:
                    self._list_channel_subscriptions.pop(key, None)

            for channel in added:
                self._list_channel_subscriptions[
                    (channel_type, channel)
                ].add(conn_id)

            subscriptions[channel_type] = channels

    async def unsubscribe_list(
        self,
        conn_id: str,
        channel_type: str,
    ) -> None:
        async with self._lock:
            subscriptions = self._list_subscriptions.get(conn_id)
            if subscriptions is None:
                return

            channels = subscriptions.pop(channel_type, set())

            for channel in channels:
                key = (channel_type, channel)
                conn_ids = self._list_channel_subscriptions.get(key)

                if conn_ids is None:
                    continue

                conn_ids.discard(conn_id)

                if not conn_ids:
                    self._list_channel_subscriptions.pop(key, None)

            if not subscriptions:
                self._list_subscriptions.pop(conn_id, None)

    async def subscribe(
        self,
        conn_id: str,
        channel_type: str,
        channel: str,
    ) -> None:
        async with self._lock:
            current = self._single_subscriptions[conn_id].get(channel_type)

            if current == channel:
                return

            if current is not None:
                self._single_channel_subscriptions[current].discard(conn_id)

                if not self._single_channel_subscriptions[current]: # 더이상 채널에 연결된 소켓이 없다면 제거
                    self._single_channel_subscriptions.pop(current, None)

            self._single_subscriptions[conn_id][channel_type] = channel
            self._single_channel_subscriptions[channel].add(conn_id)

    async def unsubscribe(
        self,
        conn_id: str,
        channel_type: str,
    ) -> None:
        async with self._lock:
            subscriptions = self._single_subscriptions.get(conn_id)
            if subscriptions is None:
                return

            channel = subscriptions.pop(channel_type, None)
            if channel is None:
                return

            self._single_channel_subscriptions[channel].discard(conn_id)

            if not self._single_channel_subscriptions[channel]:
                self._single_channel_subscriptions.pop(channel, None)

            if not subscriptions: # 더이상 남은 채널 타입이 없다면 제거
                self._single_subscriptions.pop(conn_id, None)

    async def broadcast(
        self,
        payload: dict,
    ) -> None:
        payload_type = payload["type"]

        async with self._lock:
            deliveries: list[tuple[str, WebSocket, dict]] = [] # conn_id, ws, message 전달 리스트

            if payload_type in {
                WsChannelType.CANDLE_LIST.value,
                WsChannelType.TICKER_LIST.value,
            }:
                payloads_by_conn: Dict[str, list[dict]] = defaultdict(list)

                for item in payload["data"]:
                    channel = item["channel"]
                    key = (payload_type, channel)

                    conn_ids = self._list_channel_subscriptions.get(key, set())

                    for conn_id in conn_ids:
                        payloads_by_conn[conn_id].append(item)

                for conn_id, items in payloads_by_conn.items():
                    ws = self._connections.get(conn_id)

                    if ws is None:
                        continue

                    deliveries.append(
                        (
                            conn_id,
                            ws,
                            {
                                "type": payload_type,
                                "data": items,
                            },
                        )
                    )

            else:
                channel = payload["data"]["channel"]
                conn_ids = self._single_channel_subscriptions.get(
                    channel,
                    set(),
                )

                for conn_id in conn_ids:
                    ws = self._connections.get(conn_id)

                    if ws is None:
                        continue

                    deliveries.append((conn_id, ws, payload))

        async def send(
            conn_id: str,
            ws: WebSocket,
            message: dict,
        ) -> str | None:
            try:
                async with asyncio.timeout(1): # 비동기 함수 반환의 제한 시간을 걸어서 병목 제어
                    await ws.send_json(message)
                return None
            except Exception:
                return conn_id

        results = await asyncio.gather( # 여러 비동기 함수를 동시에 진행하고 전부 끝날 때까지 대기
            *(
                send(conn_id, ws, message)
                for conn_id, ws, message in deliveries
            )
        )

        dead = {conn_id for conn_id in results if conn_id is not None}

        for conn_id in dead:
            await self.unregister(conn_id)
