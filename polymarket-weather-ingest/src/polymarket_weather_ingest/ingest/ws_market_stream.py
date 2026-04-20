from __future__ import annotations

import json
import websockets


class PolymarketMarketStream:
    WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

    def __init__(self, asset_ids: list[str]) -> None:
        self.asset_ids = [a for a in asset_ids if a]

    async def run(self, on_event) -> None:
        if not self.asset_ids:
            raise RuntimeError("No asset_ids to subscribe")

        async with websockets.connect(self.WS_URL) as ws:
            await ws.send(
                json.dumps(
                    {
                        "assets_ids": self.asset_ids,
                        "type": "market",
                    }
                )
            )

            while True:
                raw = await ws.recv()
                event = json.loads(raw)
                await on_event(event)
