from __future__ import annotations

from datetime import datetime, timezone


class MarketStateReducer:
    def __init__(self) -> None:
        self.state_by_asset: dict[str, dict] = {}

    async def on_event(self, event: dict) -> None:
        if isinstance(event, list):
            for item in event:
                await self.on_event(item)
            return

        asset_id = event.get("asset_id") or event.get("assetId")
        event_type = event.get("event_type")

        if not asset_id:
            return

        current = self.state_by_asset.get(
            str(asset_id),
            {
                "asset_id": str(asset_id),
                "updated_at": None,
                "event_type": None,
                "best_bid": None,
                "best_ask": None,
                "last_trade_price": None,
                "raw_event": None,
            },
        )

        current["updated_at"] = datetime.now(timezone.utc).isoformat()
        current["event_type"] = event_type

        if "best_bid" in event:
            current["best_bid"] = event.get("best_bid")
        if "best_ask" in event:
            current["best_ask"] = event.get("best_ask")
        if "price" in event:
            current["last_trade_price"] = event.get("price")
        if "last_trade_price" in event:
            current["last_trade_price"] = event.get("last_trade_price")

        current["raw_event"] = event
        self.state_by_asset[str(asset_id)] = current

    def snapshot(self) -> list[dict]:
        return list(self.state_by_asset.values())
