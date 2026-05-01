from backend.models.core import MarketSnapshot


class PlaceholderProbabilityProvider:
    FIXTURES = {
        "mock_weather_strong_yes": 0.72,
        "mock_weather_weak_edge": 0.51,
        "mock_low_liquidity": 0.70,
        "mock_high_spread": 0.70,
    }

    def estimate(self, market: MarketSnapshot) -> float:
        return self.FIXTURES.get(market.market_id, 0.5)
