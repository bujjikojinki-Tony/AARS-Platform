from __future__ import annotations

import json


class RealtimeRegistry:
    def build_asset_registry(self, event_payloads: list[dict]) -> list[dict]:
        registry: list[dict] = []

        for event in event_payloads:
            event_id = event.get("id")
            event_title = event.get("title") or event.get("name")
            markets = event.get("markets") or []

            for market in markets:
                token_ids = self._normalize_token_ids(
                    market.get("outcomeTokenIds") or market.get("clobTokenIds") or []
                )

                yes_asset_id = token_ids[0] if len(token_ids) >= 1 else None
                no_asset_id = token_ids[1] if len(token_ids) >= 2 else None

                registry.append(
                    {
                        "event_id": event_id,
                        "event_title": event_title,
                        "market_id": market.get("id"),
                        "market_question": market.get("question") or market.get("title"),
                        "slug": market.get("slug"),
                        "yes_asset_id": yes_asset_id,
                        "no_asset_id": no_asset_id,
                    }
                )

        return registry

    @staticmethod
    def _normalize_token_ids(value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value if item]

        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return [value] if value else []

            if isinstance(parsed, list):
                return [str(item) for item in parsed if item]

        return []
