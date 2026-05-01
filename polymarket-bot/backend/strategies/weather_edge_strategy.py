from __future__ import annotations

from uuid import uuid4

from backend.models.core import MarketSnapshot
from backend.models.core import StrategySignal
from backend.models.enums import Side


class WeatherEdgeStrategy:
    strategy_id = "weather_edge_v0"

    def __init__(self, probability_provider, min_edge_percent: float = 10):
        self.probability_provider = probability_provider
        self.min_edge_percent = min_edge_percent

    def evaluate(self, market: MarketSnapshot) -> StrategySignal | None:
        if not self._looks_like_weather_market(market):
            return None

        model_probability = self.probability_provider.estimate(market)
        market_probability = market.yes_price
        edge_percent = (model_probability - market_probability) * 100
        if abs(edge_percent) < self.min_edge_percent:
            return None

        side = Side.YES if edge_percent > 0 else Side.NO
        return StrategySignal(
            signal_id=f"sig_{uuid4().hex[:10]}",
            market_id=market.market_id,
            strategy_id=self.strategy_id,
            side=side,
            model_probability=model_probability,
            market_probability=market_probability,
            edge_percent=edge_percent,
            confidence="MEDIUM",
            reason=(
                "weather probability provider indicates model-market divergence; "
                "PWB-02 Gaussian v0 probability used"
            ),
        )

    def _looks_like_weather_market(self, market: MarketSnapshot) -> bool:
        question = market.question.lower()
        weather_keywords = [
            "temperature",
            "temp",
            "high",
            "low",
            "rain",
            "rainfall",
            "precipitation",
            "snow",
            "weather",
        ]
        return "weather" in market.market_id or any(
            keyword in question for keyword in weather_keywords
        )
