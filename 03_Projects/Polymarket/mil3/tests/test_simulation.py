from __future__ import annotations

from datetime import datetime, timedelta, timezone

from aars_market.models import Candle
from aars_market.models import MarketState, MarketStateAssessment
from aars_market.simulation import (
    EXECUTION_MODE,
    LeveragedFuturesLongGridStrategy,
    ReplayEngine,
    SpotGridStrategy,
    compare_shadow_strategies,
    simulate_aars_dynamic,
    simulate_buy_hold,
)


def _trend(n: int = 220) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candles: list[Candle] = []
    price = 100.0
    for i in range(n):
        price *= 1.001 if i < 150 else 0.9995
        candles.append(
            Candle(
                symbol="BTCUSDT",
                timeframe="1h",
                open_time=start + timedelta(hours=i),
                open=price * 0.999,
                high=price * 1.004,
                low=price * 0.996,
                close=price,
                volume=1000.0 + (300.0 if i % 24 == 0 else 0.0),
            )
        )
    return candles


def test_buy_hold_and_aars_simulations_return_finite_summaries():
    candles = _trend()
    hold = simulate_buy_hold(candles, warmup_bars=120)
    aars = simulate_aars_dynamic(candles, warmup_bars=120, max_abs_exposure=0.75)

    assert hold.strategy == "BUY_HOLD"
    assert aars.strategy == "AARS_DYNAMIC"
    assert hold.final_equity > 0
    assert aars.final_equity > 0
    assert 0 <= hold.max_drawdown <= 1
    assert 0 <= aars.max_drawdown <= 1
    assert abs(aars.final_net_exposure) <= 0.80


def _oscillating(n: int = 180) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candles: list[Candle] = []
    for i in range(n):
        close = 100.0 + (1.5 if i % 2 else -1.5)
        candles.append(
            Candle(
                symbol="SOLUSDT",
                timeframe="1h",
                open_time=start + timedelta(hours=i),
                open=100.0,
                high=102.0,
                low=98.0,
                close=close,
                volume=1000.0,
            )
        )
    return candles


def test_all_four_strategies_share_one_paper_only_replay_contract():
    summaries = compare_shadow_strategies(
        _oscillating(),
        warmup_bars=120,
        futures_leverage=10.0,
        grid_spacing_pct=0.01,
        grid_levels=2,
        tactical_hedge=False,
        fee_rate=0.0,
        slippage_rate=0.0,
        funding_rate_per_bar=0.00001,
    )

    assert [summary.strategy for summary in summaries] == [
        "BUY_HOLD",
        "SPOT_GRID",
        "FUTURES_LONG_GRID_10X",
        "AARS_DYNAMIC",
    ]
    assert all(summary.execution_mode == EXECUTION_MODE == "PAPER_ONLY" for summary in summaries)
    assert all(summary.bars == 61 for summary in summaries)
    assert all(summary.turnover_notional >= 0 for summary in summaries)
    assert all(summary.fees >= 0 and summary.slippage >= 0 for summary in summaries)
    assert summaries[2].funding != 0
    assert summaries[2].max_effective_leverage > summaries[1].max_effective_leverage
    assert summaries[2].max_liquidation_risk > summaries[1].max_liquidation_risk


def test_spot_grid_reports_realized_grid_and_inventory_pnl_separately():
    summary = ReplayEngine(fee_rate=0.0, slippage_rate=0.0).run(
        _oscillating(),
        SpotGridStrategy(spacing_pct=0.01, levels=2),
        warmup_bars=120,
    )

    assert summary.realized_grid_pnl > 0
    assert summary.realized_pnl == summary.realized_grid_pnl
    assert summary.inventory_unrealized_pnl != 0
    assert summary.profit_factor > 0


def test_10x_futures_grid_is_parameterized_and_tracks_margin_risk():
    summary = ReplayEngine(
        fee_rate=0.0,
        slippage_rate=0.0,
        funding_rate_per_bar=0.00001,
        maintenance_margin_rate=0.005,
    ).run(
        _oscillating(),
        LeveragedFuturesLongGridStrategy(
            max_leverage=10.0,
            spacing_pct=0.01,
            levels=2,
            tactical_hedge=False,
        ),
        warmup_bars=120,
    )

    assert summary.strategy == "FUTURES_LONG_GRID_10X"
    assert summary.max_effective_leverage >= 9.0
    assert summary.min_margin_buffer_pct < 0.12
    assert summary.max_liquidation_risk > 0
    assert summary.funding > 0


def test_futures_grid_adds_tactical_hedge_on_breakdown(monkeypatch):
    strategy = LeveragedFuturesLongGridStrategy(max_leverage=10.0, tactical_hedge=True, hedge_ratio=0.25)
    monkeypatch.setattr(
        "aars_market.simulation.classify_market_state",
        lambda _features: MarketStateAssessment(MarketState.BREAKDOWN, 1.0, (), ()),
    )

    actions = strategy.actions_for_bar(119, _trend(130))

    assert len(actions) == 1
    assert actions[0].category == "hedge"
    assert actions[0].target_exposure == -2.5
