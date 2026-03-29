import asyncio
from collections import defaultdict
from typing import Dict, Set

from fastapi import WebSocket


class Hub:
    def __init__(self) -> None:
        self._connections: Dict[str, WebSocket] = {}
        self._subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def register(self, conn_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._connections[conn_id] = ws
            # print("_connections", self._connections, len(self._connections))

    async def unregister(self, conn_id: str) -> None:
        async with self._lock:
            self._connections.pop(conn_id, None)

            for channel in list(self._subscriptions.keys()):
                self._subscriptions[channel].discard(conn_id)
                if not self._subscriptions[channel]:
                    del self._subscriptions[channel]

    async def subscribe(self, conn_id: str, channel: str) -> None:
        async with self._lock:
            self._subscriptions[channel].add(conn_id)

    async def unsubscribe(self, conn_id: str, channel: str) -> None:
        async with self._lock:
            self._subscriptions[channel].discard(conn_id)

    async def broadcast(self, channel: str, payload: dict) -> None:
        async with self._lock:
            conn_ids = list(self._subscriptions.get(channel, set()))
            # print(
            #     f"Broadcasting to channel '{channel}' for {len(conn_ids)} connections"
            # )
            websockets = [
                (cid, self._connections[cid])
                for cid in conn_ids
                if cid in self._connections
            ]

        dead = []
        for cid, ws in websockets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(cid)

        for cid in dead:
            await self.unregister(cid)
