from backend.models.core import MarketSnapshot


class MockMarketSource:
    def fetch_markets(self) -> list[MarketSnapshot]:
        return [
            MarketSnapshot(
                market_id="mock_weather_strong_yes",
                question="Will Tokyo high temperature exceed 30C on June 1?",
                yes_price=0.52,
                no_price=0.49,
                liquidity=1000,
                spread=0.03,
            ),
            MarketSnapshot(
                market_id="mock_weather_weak_edge",
                question="Will Osaka high temperature exceed 28C on June 1?",
                yes_price=0.50,
                no_price=0.51,
                liquidity=1000,
                spread=0.03,
            ),
            MarketSnapshot(
                market_id="mock_binary_arb",
                question="Binary arbitrage test market",
                yes_price=0.45,
                no_price=0.50,
                liquidity=1200,
                spread=0.02,
            ),
            MarketSnapshot(
                market_id="mock_low_liquidity",
                question="Will Tokyo high temperature exceed 30C on June 1?",
                yes_price=0.40,
                no_price=0.61,
                liquidity=20,
                spread=0.03,
            ),
            MarketSnapshot(
                market_id="mock_high_spread",
                question="Will Tokyo high temperature exceed 30C on June 1?",
                yes_price=0.40,
                no_price=0.63,
                liquidity=1000,
                spread=0.15,
            ),
        ]
