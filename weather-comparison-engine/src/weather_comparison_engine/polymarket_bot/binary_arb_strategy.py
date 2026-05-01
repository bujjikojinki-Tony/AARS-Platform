from __future__ import annotations

from weather_comparison_engine.polymarket_bot.models import MarketSnapshot
from weather_comparison_engine.polymarket_bot.models import StrategySignal


class BinaryArbitrageStrategy:
    strategy_id = "binary_arb_v0"

    def __init__(self, fee_buffer: float = 0.02, min_profit_percent: float = 1.0) -> None:
        self.fee_buffer = float(fee_buffer)
        self.min_profit_percent = float(min_profit_percent)

    def evaluate(
        self,
        market: MarketSnapshot,
        *,
        signal_id: str,
        created_at: str,
    ) -> StrategySignal | None:
        synthetic_total = market.yes_price + market.no_price
        theoretical_edge_percent = round((1.0 - self.fee_buffer - synthetic_total) * 100.0, 4)
        if theoretical_edge_percent < self.min_profit_percent:
            return None

        return StrategySignal(
            signal_id=signal_id,
            market_id=market.market_id,
            strategy_id=self.strategy_id,
            side="WAIT",
            model_probability=round(min(0.9999, market.yes_price + theoretical_edge_percent / 100.0), 4),
            market_probability=market.yes_price,
            edge_percent=theoretical_edge_percent,
            z_score=None,
            confidence="MEDIUM",
            reason="binary arbitrage candidate detected from underpriced YES+NO basket",
            created_at=created_at,
        )
