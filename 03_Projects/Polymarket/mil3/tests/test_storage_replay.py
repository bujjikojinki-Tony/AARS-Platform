from __future__ import annotations

from datetime import datetime, timedelta, timezone

from aars_market.models import Candle
from aars_market.replay import summarize_replay, walk_forward_replay
from aars_market.storage import MarketStore


def _candles(n: int = 180) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result: list[Candle] = []
    price = 100.0
    for i in range(n):
        # Deterministic alternating drift creates trend/range transitions without randomness.
        drift = 0.35 if (i // 30) % 2 == 0 else -0.18
        price = max(10.0, price + drift + (0.08 if i % 5 == 0 else -0.02))
        result.append(
            Candle(
                symbol="SOLUSDT",
                timeframe="1h",
                open_time=start + timedelta(hours=i),
                open=price - 0.10,
                high=price + 0.35,
                low=price - 0.40,
                close=price,
                volume=1000.0 + 20.0 * (i % 10),
            )
        )
    return result


def test_store_is_idempotent_and_chronological(tmp_path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    candles = _candles(80)

    assert store.upsert_candles(candles, source="test") == 80
    assert store.upsert_candles(candles, source="test") == 80
    assert store.count_candles("SOLUSDT", "1h") == 80

    loaded = store.load_candles("SOLUSDT", "1h", limit=10)
    assert len(loaded) == 10
    assert loaded == candles[-10:]


def test_freshness_gate(tmp_path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    candles = _candles(80)
    store.upsert_candles(candles, source="test")
    latest = candles[-1].open_time

    assert store.is_fresh(
        "SOLUSDT", "1h", now=latest + timedelta(minutes=90), max_age=timedelta(hours=2)
    )
    assert not store.is_fresh(
        "SOLUSDT", "1h", now=latest + timedelta(hours=3), max_age=timedelta(hours=2)
    )


def test_walk_forward_replay_has_no_lookahead_shape():
    candles = _candles(200)
    records = walk_forward_replay(
        candles,
        horizon_bars=24,
        warmup_bars=120,
        outcome_threshold=0.02,
    )
    assert records
    first = records[0]
    assert first.index == 119
    assert first.entry_price == candles[119].close
    assert first.exit_price == candles[143].close
    assert abs(first.probabilities.bull + first.probabilities.base + first.probabilities.bear - 1.0) < 1e-9

    summary = summarize_replay(records)
    assert summary.records == len(records)
    assert abs(summary.bull_rate + summary.base_rate + summary.bear_rate - 1.0) < 1e-9
    assert summary.mean_brier_score >= 0.0
