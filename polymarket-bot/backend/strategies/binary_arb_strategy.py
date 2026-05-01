from uuid import uuid4

from backend.models.core import MarketSnapshot
from backend.models.core import StrategySignal
from backend.models.enums import Side


class BinaryArbStrategy:
    strategy_id = "binary_arb_v0"

    def __init__(self, fee_buffer: float = 0.02, min_profit: float = 0.01):
        self.fee_buffer = fee_buffer
        self.min_profit = min_profit

    def evaluate(self, market: MarketSnapshot) -> StrategySignal | None:
        total_price = market.yes_price + market.no_price
        profit_gap = 1 - total_price
        if profit_gap <= self.fee_buffer + self.min_profit:
            return None
        return StrategySignal(
            signal_id=f"sig_{uuid4().hex[:10]}",
            market_id=market.market_id,
            strategy_id=self.strategy_id,
            side=Side.YES,
            model_probability=1.0,
            market_probability=total_price,
            edge_percent=profit_gap * 100,
            confidence="MEDIUM",
            reason="paired-arb candidate: YES + NO below 1 after fee buffer",
        )
