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
            "promotion_state": {
                "probability_mode": "heuristic_not_calibrated",
                "promotion_reason": "validation_report_stale",
                "demotion_reason": "validation_freshness_blocked",
            },
        },
        "validation": {
            "freshness_status": "warning",
            "label_coverage_status": "blocked",
            "family_rollout_summary": {
                "coverage_ratio": 1.0,
                "ready_ratio": 0.5,
                "top_family": "station_temperature",
                "top_drift_family": "sea_ice_extent",
            },
        },
        "source_policy": {
            "overall_status": "healthy",
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
    assert summary["promotion_state"] == "heuristic_not_calibrated"
    assert summary["promotion_reason"] == "validation_report_stale"
    assert summary["demotion_reason"] == "validation_freshness_blocked"
    assert summary["validation_freshness"] == "warning"
    assert summary["label_coverage"] == "blocked"
    assert summary["family_coverage_ratio"] == "100%"
    assert summary["family_ready_ratio"] == "50%"
    assert summary["family_top_family"] == "station_temperature"
    assert summary["family_top_drift_family"] == "sea_ice_extent"
    assert summary["source_policy"] == "healthy"
    assert summary["execution_status"] == "blocked"
    assert summary["can_bot_trade"] is False
    assert summary["operator_mode"] == "dry_run_guarded"
    assert summary["mode_badge_label"] == "DRY-RUN GUARDED"
    assert summary["operator_summary_line"] == "Gate blocked; review probability_mode:heuristic_not_calibrated"
    assert summary["operator_next_step"] == "review_gate_block"
    assert summary["operator_focus"] == "678686"
