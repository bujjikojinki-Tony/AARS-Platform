from weather_dashboard.ui.model_validation_panel import build_validation_summary, _validation_tone


def test_validation_summary_surfaces_promotion_blockers():
    summary = build_validation_summary(
        {
            "approved_for_live": False,
            "deployment_mode": "shadow",
            "calibration_status": "not_calibrated",
            "probability_mode": "heuristic_not_calibrated",
            "promotion_state": {
                "probability_mode": "heuristic_not_calibrated",
                "promotion_reason": "validation_report_stale",
                "demotion_reason": "validation_freshness_blocked",
            },
            "sample_count": 100,
            "labeled_sample_count": 12,
            "validation_metrics": {
                "brier_score": 0.22,
                "calibration_error": 0.18,
                "roi_backtest": -0.03,
            },
            "resolver_quality": {
                "resolver_match_rate": 0.8,
                "unmatched_count": 2,
            },
        },
        {"model_probability": {"reliability_curve": [{"bucket": 1}]}},
        {"trade_count": 5, "roi": 0.01},
        {"status": "blocked", "freshness_seconds": 999},
        {"status": "blocked", "labeled_ratio": 0.12, "minimum_labeled_rows": 30},
    )

    assert summary["approved_for_live"] is False
    assert summary["coverage_status"] == "blocked"
    assert summary["freshness_status"] == "blocked"
    assert summary["promotion_state"] == "heuristic_not_calibrated"
    assert summary["promotion_reason"] == "validation_report_stale"
    assert summary["demotion_reason"] == "validation_freshness_blocked"
    assert summary["calibration_curve_points"] == 1
    assert "not_approved_for_live" in summary["blockers"]
    assert "calibration:not_calibrated" in summary["blockers"]


def test_validation_tone_maps_statuses():
    assert _validation_tone("healthy") == "ok"
    assert _validation_tone("blocked") == "block"
    assert _validation_tone("warning") == "warn"
    assert _validation_tone("unknown") == "neutral"
