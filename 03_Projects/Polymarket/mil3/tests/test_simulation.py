from __future__ import annotations

from datetime import datetime, timedelta, timezone

from aars_market.models import Candle
from aars_market.simulation import simulate_aars_dynamic, simulate_buy_hold


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
