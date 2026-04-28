from weather_dashboard.ui.operator_focus_panel import build_operator_focus_summary


def test_operator_focus_summary_prioritizes_gate_and_probability_fields():
    summary = build_operator_focus_summary(
        market_snapshot={
            "market_id": "123",
            "market_question": "Will Shanghai have a high temperature above 35C?",
            "market_family": "temperature_daily_max",
            "target_date": "2026-04-20",
            "market_probability": 0.62,
        },
        forecast_snapshot={"updated_at": "2026-04-19T10:00:00Z"},
        probability_state={
            "probability_mode": "heuristic_not_calibrated",
            "execution_constraint": "manual_advisory_only",
            "confidence_adjusted_edge": -0.031,
            "promotion_state": {
                "probability_mode": "heuristic_not_calibrated",
                "promotion_reason": "validation_report_stale",
                "demotion_reason": "validation_freshness_blocked",
            },
        },
        comparison_row={
            "comparison_status": "strong_divergence",
            "confidence_adjusted_gap": -0.18,
        },
        compact_gate_summary={
            "gate_status": "BLOCKED",
            "severity": "high",
            "resolver_gate": "pass",
            "freshness_gate": "blocked",
            "authorization_gate": "blocked",
            "execution_gate": "blocked",
            "gate_source": "api",
            "recommended_operator_action": "refresh_pipeline_inputs",
            "blockers": ["stale_worker", "probability_not_calibrated"],
        },
        unified_status_report={"operator": {"operator_mode": "dry_run_guarded"}},
    )

    assert summary["market_id"] == "123"
    assert summary["gate_status"] == "BLOCKED"
    assert summary["probability_mode"] == "heuristic_not_calibrated"
    assert summary["execution_constraint"] == "manual_advisory_only"
    assert summary["promotion_state"] == "heuristic_not_calibrated"
    assert summary["promotion_reason"] == "validation_report_stale"
    assert summary["demotion_reason"] == "validation_freshness_blocked"
    assert summary["freshness_gate"] == "blocked"
    assert summary["recommended_action"] == "refresh_pipeline_inputs"
    assert summary["block_reasons"] == ["stale_worker", "probability_not_calibrated"]


def test_operator_focus_summary_handles_string_promotion_state() -> None:
    summary = build_operator_focus_summary(
        market_snapshot={"market_id": "123", "market_question": "Q", "market_family": "temperature_daily_max"},
        forecast_snapshot={},
        probability_state={
            "probability_mode": "heuristic_not_calibrated",
            "execution_constraint": "manual_advisory_only",
            "promotion_state": "heuristic_not_calibrated",
        },
        comparison_row={"comparison_status": "aligned"},
        compact_gate_summary={"gate_status": "READY", "blockers": []},
        unified_status_report={"operator": {"operator_mode": "dry_run_guarded"}},
    )

    assert summary["promotion_state"] == "heuristic_not_calibrated"
    assert summary["promotion_reason"] == "-"
    assert summary["demotion_reason"] == "-"


def test_operator_focus_summary_handles_non_dict_inputs() -> None:
    summary = build_operator_focus_summary(
        market_snapshot="bad",
        forecast_snapshot="bad",
        probability_state="bad",
        comparison_row="bad",
        compact_gate_summary="bad",
        unified_status_report="bad",
    )

    assert summary["market_id"] == "-"
    assert summary["probability_mode"] == "-"
    assert summary["promotion_state"] == "-"
