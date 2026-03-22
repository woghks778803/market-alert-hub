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

    async def unregister(self, conn_id: str) -> None:
        async with self._lock:
            self._connections.pop(conn_id, None)

            for symbol in list(self._subscriptions.keys()):
                self._subscriptions[symbol].discard(conn_id)
                if not self._subscriptions[symbol]:
                    del self._subscriptions[symbol]

    async def subscribe(self, conn_id: str, symbol: str) -> None:
        async with self._lock:
            self._subscriptions[symbol].add(conn_id)

    async def unsubscribe(self, conn_id: str, symbol: str) -> None:
        async with self._lock:
            self._subscriptions[symbol].discard(conn_id)

    async def broadcast(self, symbol: str, payload: dict) -> None:
        async with self._lock:
            conn_ids = list(self._subscriptions.get(symbol, set()))
            websockets = [
                self._connections[cid] for cid in conn_ids if cid in self._connections
            ]

        for ws in websockets:
            await ws.send_json(payload)
