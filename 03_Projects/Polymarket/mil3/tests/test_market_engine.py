from datetime import datetime, timedelta, timezone

import pytest

from aars_market.features import compute_features
from aars_market.models import Candle, MarketState
from aars_market.probability import estimate_outcome_probabilities
from aars_market.state_engine import classify_market_state


def candles(slope: float, n: int = 100) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = []
    for i in range(n):
        close = 100.0 + slope * i
        result.append(Candle(
            symbol="SOLUSDT",
            timeframe="1h",
            open_time=start + timedelta(hours=i),
            open=close - slope * 0.2,
            high=close + 1.0,
            low=close - 1.0,
            close=close,
            volume=1000.0 + i * 2,
        ))
    return result


def test_feature_engine_requires_60_candles():
    with pytest.raises(ValueError):
        compute_features(candles(0.1, 59))


def test_uptrend_is_not_classified_as_breakdown():
    assessment = classify_market_state(compute_features(candles(0.35)))
    assert assessment.state in {MarketState.RECOVERY, MarketState.TREND_EXPANSION, MarketState.BREAKOUT}
    assert assessment.evidence


def test_downtrend_is_bearish_state():
    assessment = classify_market_state(compute_features(candles(-0.35)))
    assert assessment.state in {MarketState.DISTRIBUTION, MarketState.BREAKDOWN, MarketState.ACCUMULATION}


def test_probabilities_sum_to_one():
    assessment = classify_market_state(compute_features(candles(0.2)))
    p = estimate_outcome_probabilities(assessment)
    assert p.bull + p.base + p.bear == pytest.approx(1.0)
    assert min(p.bull, p.base, p.bear) >= 0.0
