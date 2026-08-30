from __future__ import annotations

import pytest

from aars_market.models import MarketState, MarketStateAssessment, OutcomeProbabilities
from aars_market.paper import PaperPortfolio
from aars_market.policy import decide_target_exposure


def test_long_trade_then_partial_close_realizes_pnl():
    p = PaperPortfolio(1000.0, fee_rate=0.0, slippage_rate=0.0)
    p.trade(2.0, 100.0)
    p.trade(-1.0, 110.0)
    snap = p.snapshot(110.0)
    assert snap.position_qty == 1.0
    assert snap.avg_entry == 100.0
    assert snap.realized_pnl == 10.0
    assert snap.unrealized_pnl == 10.0
    assert snap.equity == 1020.0


def test_cross_from_long_to_short_resets_entry():
    p = PaperPortfolio(1000.0, fee_rate=0.0, slippage_rate=0.0)
    p.trade(1.0, 100.0)
    p.trade(-2.0, 90.0)
    snap = p.snapshot(80.0)
    assert snap.position_qty == -1.0
    assert snap.avg_entry == 90.0
    assert snap.realized_pnl == -10.0
    assert snap.unrealized_pnl == 10.0
    assert snap.equity == 1000.0


def test_funding_positive_rate_charges_long_and_credits_short():
    long = PaperPortfolio(1000.0, fee_rate=0.0, slippage_rate=0.0)
    long.trade(1.0, 100.0)
    assert long.apply_funding_rate(100.0, 0.001) == 0.1
    assert long.snapshot(100.0).equity == 999.9

    short = PaperPortfolio(1000.0, fee_rate=0.0, slippage_rate=0.0)
    short.trade(-1.0, 100.0)
    assert short.apply_funding_rate(100.0, 0.001) == -0.1
    assert short.snapshot(100.0).equity == 1000.1


def test_policy_is_bounded_and_directionally_consistent():
    bullish = MarketStateAssessment(MarketState.TREND_EXPANSION, 0.8, (), ())
    bearish = MarketStateAssessment(MarketState.BREAKDOWN, 0.8, (), ())
    bull_probs = OutcomeProbabilities(0.60, 0.25, 0.15, 24)
    bear_probs = OutcomeProbabilities(0.15, 0.25, 0.60, 24)

    long_decision = decide_target_exposure(bullish, bull_probs, max_abs_exposure=0.5)
    short_decision = decide_target_exposure(bearish, bear_probs, max_abs_exposure=0.5)

    assert 0 < long_decision.target_exposure <= 0.5
    assert -0.5 <= short_decision.target_exposure < 0


def test_slippage_and_liquidation_risk_are_explicit():
    p = PaperPortfolio(1000.0, fee_rate=0.001, slippage_rate=0.002)
    trade = p.rebalance_to_exposure(10.0, 100.0, max_leverage=10.0)

    assert trade is not None
    assert trade.execution_price == 100.2
    assert trade.slippage_cost == pytest.approx(20.0)
    assert trade.fee == pytest.approx(10.02)

    snap = p.snapshot(100.0, maintenance_margin_rate=0.005)
    assert snap.slippage_cost == pytest.approx(20.0)
    assert snap.effective_leverage > 10.0  # costs reduce equity after the target sizing decision
    assert 0 < snap.margin_buffer_pct < 0.10
    assert 0 < snap.liquidation_risk < 1.0
    assert not snap.liquidation_breached
