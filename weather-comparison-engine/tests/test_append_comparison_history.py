from weather_comparison_engine.outputs.append_comparison_history import ComparisonHistoryAppender


def test_comparison_history_appender(tmp_path):
    path = tmp_path / "comparison_history.json"
    appender = ComparisonHistoryAppender(str(path))

    appender.append({"market_id": "m1", "timestamp": "2026-04-11T00:00:00"})
    appender.append({"market_id": "m2", "timestamp": "2026-04-11T06:00:00"})

    rows = appender.load()
    assert len(rows) == 2
    assert rows[0]["market_id"] == "m1"


def test_comparison_history_appender_dedupes(tmp_path):
    path = tmp_path / "comparison_history.json"
    appender = ComparisonHistoryAppender(str(path))

    assert (
        appender.append(
            {
                "market_id": "m1",
                "model_band": "28",
                "market_band": "27",
                "comparison_status": "mild_divergence",
                "action_hint": "watch",
                "confidence_adjusted_gap": 0.8,
            }
        )
        is True
    )
    assert (
        appender.append(
            {
                "market_id": "m1",
                "model_band": "28",
                "market_band": "27",
                "comparison_status": "mild_divergence",
                "action_hint": "watch",
                "confidence_adjusted_gap": 0.8,
            }
        )
        is False
    )
