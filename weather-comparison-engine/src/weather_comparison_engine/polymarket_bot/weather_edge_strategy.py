from __future__ import annotations

from weather_comparison_engine.polymarket_bot.models import MarketSnapshot
from weather_comparison_engine.polymarket_bot.models import StrategySignal


class WeatherEdgeStrategy:
    strategy_id = "weather_edge_v0"

    def __init__(self, probability_provider, min_edge_percent: float = 10.0) -> None:
        self.probability_provider = probability_provider
        self.min_edge_percent = float(min_edge_percent)

    def evaluate(
        self,
        market: MarketSnapshot,
        *,
        signal_id: str,
        created_at: str,
    ) -> StrategySignal | None:
        model_probability = self.probability_provider.estimate(market)
        market_probability = market.yes_price
        edge_percent = round((model_probability - market_probability) * 100.0, 4)
        if abs(edge_percent) < self.min_edge_percent:
            return None

        side = "YES" if edge_percent > 0 else "NO"
        confidence = self._confidence_for_edge(edge_percent)
        return StrategySignal(
            signal_id=signal_id,
            market_id=market.market_id,
            strategy_id=self.strategy_id,
            side=side,
            model_probability=model_probability,
            market_probability=market_probability,
            edge_percent=edge_percent,
            z_score=round(abs(edge_percent) / 10.0, 2),
            confidence=confidence,
            reason="placeholder probability engine indicates model-market divergence",
            created_at=created_at,
        )

    @staticmethod
    def _confidence_for_edge(edge_percent: float) -> str:
        magnitude = abs(edge_percent)
        if magnitude >= 18.0:
            return "HIGH"
        if magnitude >= 12.0:
            return "MEDIUM"
        return "LOW"
