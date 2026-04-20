class ExposureLimits:
    def __init__(self, max_notional_per_market: float, max_total_notional: float) -> None:
        self.max_notional_per_market = max_notional_per_market
        self.max_total_notional = max_total_notional

    def allows(self, market_notional: float, total_notional: float, new_order_notional: float) -> bool:
        if market_notional + new_order_notional > self.max_notional_per_market:
            return False

        if total_notional + new_order_notional > self.max_total_notional:
            return False

        return True
