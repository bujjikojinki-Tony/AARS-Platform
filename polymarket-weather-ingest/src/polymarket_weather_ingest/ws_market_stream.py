from __future__ import annotations

import json


class PolymarketMarketStream:
    WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

    def __init__(self, asset_ids: list[str]) -> None:
        self.asset_ids = [asset_id for asset_id in asset_ids if asset_id]

    async def run(self, on_event) -> None:
        if not self.asset_ids:
            raise RuntimeError("No asset_ids to subscribe")

        import websockets

        async with websockets.connect(self.WS_URL) as ws:
            sub_msg = {
                "assets_ids": self.asset_ids,
                "type": "market",
                "custom_feature_enabled": True,
            }
            await ws.send(json.dumps(sub_msg))

            while True:
                raw = await ws.recv()
                event = json.loads(raw)
                await on_event(event)
