from weather_dashboard.ui.operator_context_badge import build_operator_context_badge_context


def test_build_operator_context_badge_context() -> None:
    summary = build_operator_context_badge_context(
        {
            "market_id": "678687",
            "label": "Second hottest year",
            "selection_source": "watchlist",
            "market_family": "global_temperature_index",
            "comparison_status": "mild_divergence",
            "action_hint": "watch",
            "probability_mode": "heuristic_not_calibrated",
            "generated_at": "2026-04-19T01:00:00+00:00",
        }
    )

    assert summary is not None
    assert summary["market_id"] == "678687"
    assert summary["label"] == "Second hottest year"
    assert summary["selection_source"] == "watchlist"
    assert summary["comparison_status"] == "mild_divergence"


def test_build_operator_context_badge_context_returns_none_without_market() -> None:
    assert build_operator_context_badge_context({"market_id": ""}) is None
