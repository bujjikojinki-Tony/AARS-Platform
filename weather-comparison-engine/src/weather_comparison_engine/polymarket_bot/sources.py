from __future__ import annotations

from weather_comparison_engine.polymarket_bot.models import MarketSnapshot


class MockMarketSource:
    def fetch_markets(self) -> list[MarketSnapshot]:
        return [
            MarketSnapshot(
                market_id="mock_ny_rain_50",
                question="Will rainfall exceed 50mm in New York on 2026-04-29?",
                slug="new-york-rainfall-50mm",
                category="weather",
                yes_price=0.41,
                no_price=0.59,
                liquidity=125_000.0,
                spread=0.03,
                fetched_at="2026-04-28T10:00:00Z",
            ),
            MarketSnapshot(
                market_id="mock_ldn_snow_5",
                question="Will snowfall exceed 5cm in London on 2026-04-29?",
                slug="london-snowfall-5cm",
                category="weather",
                yes_price=0.27,
                no_price=0.73,
                liquidity=86_000.0,
                spread=0.04,
                fetched_at="2026-04-28T10:00:00Z",
            ),
            MarketSnapshot(
                market_id="mock_hou_temp_35",
                question="Will max temperature exceed 35C in Houston on 2026-04-29?",
                slug="houston-max-temp-35c",
                category="weather",
                yes_price=0.63,
                no_price=0.37,
                liquidity=94_500.0,
                spread=0.02,
                fetched_at="2026-04-28T10:00:00Z",
            ),
            MarketSnapshot(
                market_id="mock_tyo_typhoon_landfall",
                question="Will a typhoon make landfall near Tokyo before 2026-05-03?",
                slug="tokyo-typhoon-landfall",
                category="weather",
                yes_price=0.18,
                no_price=0.82,
                liquidity=57_200.0,
                spread=0.05,
                fetched_at="2026-04-28T10:00:00Z",
            ),
            MarketSnapshot(
                market_id="mock_syd_wind_30",
                question="Will wind exceed 30kt in Sydney on 2026-04-29?",
                slug="sydney-wind-30kt",
                category="weather",
                yes_price=0.36,
                no_price=0.64,
                liquidity=48_900.0,
                spread=0.06,
                fetched_at="2026-04-28T10:00:00Z",
            ),
            MarketSnapshot(
                market_id="mock_ber_snow_2",
                question="Will snowfall exceed 2cm in Berlin on 2026-04-29?",
                slug="berlin-snow-2cm",
                category="weather",
                yes_price=0.54,
                no_price=0.46,
                liquidity=72_300.0,
                spread=0.03,
                fetched_at="2026-04-28T10:00:00Z",
            ),
        ]
