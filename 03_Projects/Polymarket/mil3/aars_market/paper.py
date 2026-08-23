from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PaperSnapshot:
    mark_price: float
    position_qty: float
    avg_entry: float | None
    realized_pnl: float
    unrealized_pnl: float
    fees: float
    funding: float
    equity: float
    net_exposure: float
    effective_leverage: float
    margin_buffer_pct: float
    max_drawdown: float


class PaperPortfolio:
    """Single-symbol paper derivatives ledger.

    The ledger is deliberately exchange-agnostic and has no order connector.
    Fees, slippage and funding are explicit so strategy comparisons do not get
    a free execution assumption.
    """

    def __init__(
        self,
        initial_equity: float = 1000.0,
        *,
        fee_rate: float = 0.0005,
        slippage_rate: float = 0.0002,
    ) -> None:
        if initial_equity <= 0:
            raise ValueError("initial_equity must be positive")
        if fee_rate < 0 or slippage_rate < 0:
            raise ValueError("fee/slippage rates must be non-negative")
        self.initial_equity = float(initial_equity)
        self.fee_rate = float(fee_rate)
        self.slippage_rate = float(slippage_rate)
        self.position_qty = 0.0
        self.avg_entry: float | None = None
        self.realized_pnl = 0.0
        self.fees = 0.0
        self.funding = 0.0
        self.peak_equity = float(initial_equity)
        self.max_drawdown = 0.0

    def _execution_price(self, price: float, delta_qty: float) -> float:
        if price <= 0:
            raise ValueError("price must be positive")
        if delta_qty > 0:
            return price * (1.0 + self.slippage_rate)
        if delta_qty < 0:
            return price * (1.0 - self.slippage_rate)
        return price

    def trade(self, delta_qty: float, price: float) -> None:
        if delta_qty == 0:
            return
        execution_price = self._execution_price(price, delta_qty)
        self.fees += abs(delta_qty) * execution_price * self.fee_rate

        old_qty = self.position_qty
        new_qty = old_qty + delta_qty

        if old_qty == 0 or old_qty * delta_qty > 0:
            old_notional = abs(old_qty) * (self.avg_entry or execution_price)
            added_notional = abs(delta_qty) * execution_price
            self.position_qty = new_qty
            self.avg_entry = (old_notional + added_notional) / abs(new_qty)
            return

        # Opposite-side trade closes some or all of the old position first.
        close_qty = min(abs(old_qty), abs(delta_qty))
        direction = 1.0 if old_qty > 0 else -1.0
        assert self.avg_entry is not None
        self.realized_pnl += close_qty * (execution_price - self.avg_entry) * direction

        self.position_qty = new_qty
        if new_qty == 0:
            self.avg_entry = None
        elif old_qty * new_qty > 0:
            # Partial close: surviving inventory keeps its historical entry.
            pass
        else:
            # Position crossed through zero; residual starts at this execution.
            self.avg_entry = execution_price

    def apply_funding_rate(self, mark_price: float, funding_rate: float) -> float:
        """Apply one funding event; positive rate means longs pay shorts."""
        if mark_price <= 0:
            raise ValueError("mark_price must be positive")
        payment = self.position_qty * mark_price * funding_rate
        self.funding += payment
        return payment

    def unrealized_pnl(self, mark_price: float) -> float:
        if self.position_qty == 0 or self.avg_entry is None:
            return 0.0
        direction = 1.0 if self.position_qty > 0 else -1.0
        return abs(self.position_qty) * (mark_price - self.avg_entry) * direction

    def equity(self, mark_price: float) -> float:
        return self.initial_equity + self.realized_pnl + self.unrealized_pnl(mark_price) - self.fees - self.funding

    def rebalance_to_exposure(self, target_exposure: float, mark_price: float, max_leverage: float = 1.0) -> float:
        """Trade toward a signed target notional/equity ratio.

        target_exposure=+0.5 means +50% notional long; -0.5 means 50% short.
        Exposure is clipped to max_leverage. Returns executed delta quantity.
        """
        if max_leverage <= 0:
            raise ValueError("max_leverage must be positive")
        target = max(-max_leverage, min(max_leverage, target_exposure))
        current_equity = self.equity(mark_price)
        if current_equity <= 0:
            raise RuntimeError("paper portfolio equity is non-positive")
        target_notional = target * current_equity
        target_qty = target_notional / mark_price
        delta_qty = target_qty - self.position_qty
        self.trade(delta_qty, mark_price)
        return delta_qty

    def snapshot(self, mark_price: float) -> PaperSnapshot:
        unrealized = self.unrealized_pnl(mark_price)
        equity = self.equity(mark_price)
        notional = self.position_qty * mark_price
        net_exposure = notional / equity if equity > 0 else 0.0
        leverage = abs(notional) / equity if equity > 0 else float("inf")
        margin_buffer = 1.0 / leverage if leverage > 0 and leverage != float("inf") else (0.0 if leverage == float("inf") else 1.0)

        if equity > self.peak_equity:
            self.peak_equity = equity
        drawdown = (self.peak_equity - equity) / self.peak_equity if self.peak_equity > 0 else 0.0
        self.max_drawdown = max(self.max_drawdown, drawdown)

        return PaperSnapshot(
            mark_price=mark_price,
            position_qty=self.position_qty,
            avg_entry=self.avg_entry,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=unrealized,
            fees=self.fees,
            funding=self.funding,
            equity=equity,
            net_exposure=net_exposure,
            effective_leverage=leverage,
            margin_buffer_pct=margin_buffer,
            max_drawdown=self.max_drawdown,
        )
