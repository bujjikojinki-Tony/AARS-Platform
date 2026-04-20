from __future__ import annotations


class RealtimeRegistry:
    def build_asset_registry(self, event_payloads: list[dict]) -> list[dict]:
        registry: list[dict] = []

        for event in event_payloads:
            event_title = event.get("title") or event.get("name")
            markets = event.get("markets") or []

            for market in markets:
                outcome_token_ids = market.get("outcomeTokenIds")
                yes_asset_id = None
                no_asset_id = None

                if isinstance(outcome_token_ids, list):
                    yes_asset_id = outcome_token_ids[0] if len(outcome_token_ids) > 0 else None
                    no_asset_id = outcome_token_ids[1] if len(outcome_token_ids) > 1 else None

                registry.append(
                    {
                        "event_id": event.get("id"),
                        "event_title": event_title,
                        "market_id": market.get("id"),
                        "market_question": market.get("question") or market.get("title"),
                        "slug": market.get("slug"),
                        "yes_asset_id": yes_asset_id,
                        "no_asset_id": no_asset_id,
                    }
                )

        return registry
