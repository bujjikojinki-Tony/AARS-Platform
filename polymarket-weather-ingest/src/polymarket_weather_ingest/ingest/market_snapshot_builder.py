from polymarket_weather_ingest.models.market_content import MarketContent
from polymarket_weather_ingest.models.market_price_state import MarketPriceState
from polymarket_weather_ingest.models.weather_market_bundle import WeatherMarketBundle


class MarketSnapshotBuilder:
    def build_from_event(self, event_payload: dict) -> WeatherMarketBundle:
        event_id = event_payload.get("id")
        title = event_payload.get("title") or event_payload.get("name")

        markets = event_payload.get("markets") or []
        first_market = markets[0] if markets else {}

        market = MarketContent(
            event_id=str(event_id) if event_id is not None else None,
            event_title=title,
            market_id=str(first_market.get("id")) if first_market.get("id") is not None else None,
            market_question=first_market.get("question") or first_market.get("title"),
            market_slug=first_market.get("slug"),
            category=event_payload.get("category"),
            active=event_payload.get("active"),
            closed=event_payload.get("closed"),
            volume_24hr=self._to_float(first_market.get("volume24hr")),
            liquidity=self._to_float(first_market.get("liquidity")),
        )

        price_state = MarketPriceState(
            observed_at=None,
            favored_outcome=None,
            favored_probability=None,
            implied_band=None,
            notes="MVP builder: metadata only, no CLOB price integration yet",
        )

        return WeatherMarketBundle(
            market=market,
            price_state=price_state,
        )

    @staticmethod
    def _to_float(value):
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
