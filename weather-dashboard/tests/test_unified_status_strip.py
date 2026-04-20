from weather_dashboard.ui.unified_status_strip import build_unified_status_strip_summary


def test_build_unified_status_strip_summary() -> None:
    report = {
        "overall_status": "guarded",
        "current_market": {
            "market_id": "678686",
            "comparison_status": "aligned",
        },
        "probability": {
            "probability_mode": "heuristic_not_calibrated",
            "execution_constraint": "manual_advisory_only",
        },
        "validation": {
            "freshness_status": "warning",
            "label_coverage_status": "blocked",
        },
        "execution": {
            "status": "blocked",
        },
        "operator": {
            "can_bot_trade": False,
            "operator_mode": "dry_run_guarded",
            "mode_badge": {"label": "DRY-RUN GUARDED"},
        },
        "block_reasons": [
            "probability_mode:heuristic_not_calibrated",
            "execution:blocked",
        ],
    }

    summary = build_unified_status_strip_summary(report)

    assert summary is not None
    assert summary["overall_status"] == "guarded"
    assert summary["market_id"] == "678686"
    assert summary["probability_mode"] == "heuristic_not_calibrated"
    assert summary["validation_freshness"] == "warning"
    assert summary["label_coverage"] == "blocked"
    assert summary["execution_status"] == "blocked"
    assert summary["can_bot_trade"] is False
    assert summary["operator_mode"] == "dry_run_guarded"
    assert summary["mode_badge_label"] == "DRY-RUN GUARDED"
