import json

from weather_comparison_engine.outputs.history_appender import ComparisonHistoryAppender


def test_history_appender_dedupes_per_market(tmp_path):
    path = tmp_path / "comparison_history.json"
    appender = ComparisonHistoryAppender(path=str(path), max_rows_per_market=10)

    point_a1 = {
        "timestamp": "2026-04-11T00:00:00",
        "market_id": "market_a",
        "model_band": "28",
        "market_band": "27",
        "comparison_status": "mild_divergence",
        "action_hint": "watch",
        "confidence_adjusted_gap": 0.8,
    }

    point_a2 = {
        **point_a1,
        "timestamp": "2026-04-11T00:05:00",
    }

    point_b1 = {
        "timestamp": "2026-04-11T00:01:00",
        "market_id": "market_b",
        "model_band": "27",
        "market_band": "27",
        "comparison_status": "aligned",
        "action_hint": "watch",
        "confidence_adjusted_gap": 0.0,
    }

    first = appender.append(point_a1)
    second = appender.append(point_b1)
    third = appender.append(point_a2)

    rows = json.loads(path.read_text(encoding="utf-8"))

    assert first is True
    assert second is True
    assert third is False
    assert len(rows) == 2


def test_history_appender_keeps_market_probability_changes(tmp_path):
    path = tmp_path / "comparison_history.json"
    appender = ComparisonHistoryAppender(path=str(path), max_rows_per_market=10)

    base_point = {
        "timestamp": "2026-04-11T00:00:00",
        "market_id": "market_a",
        "model_band": "28",
        "market_band": "27",
        "comparison_status": "mild_divergence",
        "action_hint": "watch",
        "confidence_adjusted_gap": 0.8,
        "market_probability": 0.61,
        "favored_side": "yes",
        "yes_price": 0.61,
        "no_price": 0.39,
    }

    next_point = {
        **base_point,
        "timestamp": "2026-04-11T00:05:00",
        "market_probability": 0.64,
        "yes_price": 0.64,
        "no_price": 0.36,
    }

    first = appender.append(base_point)
    second = appender.append(next_point)

    rows = json.loads(path.read_text(encoding="utf-8"))

    assert first is True
    assert second is True
    assert len(rows) == 2


def test_history_appender_truncates_per_market(tmp_path):
    path = tmp_path / "comparison_history.json"
    appender = ComparisonHistoryAppender(path=str(path), max_rows_per_market=2)

    rows = [
        {
            "timestamp": "2026-04-11T00:00:00",
            "market_id": "market_a",
            "model_band": "26",
            "market_band": "27",
            "comparison_status": "mild_divergence",
            "action_hint": "watch",
            "confidence_adjusted_gap": 0.5,
        },
        {
            "timestamp": "2026-04-11T00:01:00",
            "market_id": "market_a",
            "model_band": "27",
            "market_band": "27",
            "comparison_status": "aligned",
            "action_hint": "watch",
            "confidence_adjusted_gap": 0.0,
        },
        {
            "timestamp": "2026-04-11T00:02:00",
            "market_id": "market_a",
            "model_band": "28",
            "market_band": "27",
            "comparison_status": "mild_divergence",
            "action_hint": "approve_small",
            "confidence_adjusted_gap": 0.9,
        },
        {
            "timestamp": "2026-04-11T00:03:00",
            "market_id": "market_b",
            "model_band": "27",
            "market_band": "28",
            "comparison_status": "mild_divergence",
            "action_hint": "watch",
            "confidence_adjusted_gap": 0.7,
        },
    ]

    for row in rows:
        appender.append(row)

    saved = json.loads(path.read_text(encoding="utf-8"))

    market_a_rows = [r for r in saved if r["market_id"] == "market_a"]
    market_b_rows = [r for r in saved if r["market_id"] == "market_b"]

    assert len(market_a_rows) == 2
    assert len(market_b_rows) == 1
    assert market_a_rows[0]["model_band"] == "27"
    assert market_a_rows[1]["model_band"] == "28"
