from datetime import datetime, timezone

from weather_comparison_engine.status import UnifiedStatusBuilder


def test_unified_status_builder_marks_guarded_when_probability_not_live() -> None:
    builder = UnifiedStatusBuilder(now=datetime(2026, 4, 18, 8, 0, tzinfo=timezone.utc))

    payload = builder.build(
        monitoring_report={
            "overall_status": "healthy",
            "counts": {"healthy": 2, "warning": 0, "stale": 0, "missing": 0},
            "workers": [
                {"label": "Market", "layer": "market_layer", "status": "healthy", "freshness_seconds": 12},
                {"label": "Forecast", "layer": "resolver_layer", "status": "healthy", "freshness_seconds": 15},
            ],
        },
        latest_dashboard_rows=[
            {
                "market_id": "m1",
                "market_question": "Will 2026 be the hottest year on record?",
                "comparison_status": "aligned",
                "confidence_adjusted_gap": 0.0,
                "action_hint": "watch",
                "market_probability": 0.67,
                "rule_status": "matched_index",
                "resolver_confidence": 0.6,
                "source_match_grade": "family_only",
            }
        ],
        probability_shadow_report={
            "states": [
                {
                    "market_id": "m1",
                    "probability_mode": "heuristic_not_calibrated",
                    "execution_constraint": "manual_advisory_only",
                    "calibration_status": "not_calibrated",
                    "probability_contract": {
                        "contract_version": "probability_contract.v1",
                        "probability_mode": "heuristic_not_calibrated",
                        "execution_constraint": "manual_advisory_only",
                        "calibration_status": "not_calibrated",
                    },
                    "confidence_adjusted_edge": 0.04,
                }
            ]
        },
        production_readiness_report={
            "status": "blocked",
            "ready_for_live": False,
            "decision": "LIVE_EXECUTION_BLOCKED",
            "blocking_count": 2,
            "warning_count": 0,
        },
        validation_freshness_status={
            "status": "warning",
            "reason": "validation_report_aging",
            "freshness_seconds": 2400,
        },
        label_coverage_report={
            "status": "blocked",
            "labeled_rows": 10,
            "labeled_ratio": 0.1,
            "blockers": ["labeled_rows_below_min"],
        },
    )

    assert payload["schema_version"] == "unified_status.v1"
    assert payload["overall_status"] == "guarded"
    assert payload["operator"]["can_bot_trade"] is False
    assert payload["operator"]["operator_mode"] == "dry_run_guarded"
    assert payload["operator"]["dev_controls_enabled"] is False
    assert "probability_mode:heuristic_not_calibrated" in payload["block_reasons"]
    assert "validation_freshness:warning" in payload["block_reasons"]
    assert "label_coverage:blocked" in payload["block_reasons"]
    assert payload["current_market"]["market_id"] == "m1"
    assert payload["top_parameter_view"]["schema_version"] == "top_parameter_view.v1"
    assert payload["probability"]["contract_version"] == "probability_contract.v1"
    assert payload["probability"]["probability_contract"]["execution_constraint"] == "manual_advisory_only"
    assert payload["validation"]["promotion_state"]["probability_mode"] == "heuristic_not_calibrated"
    assert payload["gate_stack"]["resolver_gate"] == "blocked"
    assert "resolver_confidence_low" in payload["gate_stack"]["resolver_gate_reasons"]
    assert payload["gate_stack"]["authorization_gate"] == "blocked"


def test_unified_status_builder_marks_live_ready_when_all_green() -> None:
    builder = UnifiedStatusBuilder(now=datetime(2026, 4, 18, 8, 0, tzinfo=timezone.utc))

    payload = builder.build(
        monitoring_report={
            "overall_status": "healthy",
            "counts": {"healthy": 6, "warning": 0, "stale": 0, "missing": 0},
            "workers": [
                {"label": "Market", "layer": "market_layer", "status": "healthy", "freshness_seconds": 12},
            ],
        },
        latest_dashboard_rows=[
            {
                "market_id": "m2",
                "market_question": "Will snow exceed 10cm?",
                "comparison_status": "aligned",
                "confidence_adjusted_gap": 0.0,
                "action_hint": "approve_small",
                "market_probability": 0.58,
                "rule_status": "matched",
                "resolver_confidence": 0.9,
                "source_match_grade": "exact_station",
            }
        ],
        probability_shadow_report={
            "states": [
                {
                    "market_id": "m2",
                    "probability_mode": "live_approved",
                    "execution_constraint": "live_execution_allowed",
                    "calibration_status": "calibrated",
                    "confidence_adjusted_edge": 0.12,
                }
            ]
        },
        production_readiness_report={
            "status": "ready",
            "ready_for_live": True,
            "decision": "LIVE_EXECUTION_ALLOWED",
            "blocking_count": 0,
            "warning_count": 0,
        },
        validation_freshness_status={
            "status": "healthy",
            "reason": "validation_report_fresh",
            "freshness_seconds": 300,
        },
        label_coverage_report={
            "status": "healthy",
            "labeled_rows": 300,
            "labeled_ratio": 0.75,
            "blockers": [],
        },
        source_policy_status={
            "schema_version": "source_policy_status.v1",
            "overall_status": "healthy",
            "registry_schema_version": "source_policy_registry.v1",
            "counts": {"fresh": 4, "stale": 0, "unavailable": 0},
            "priority_counts": {"critical": 1, "high": 2, "medium": 1},
            "problem_sources": [],
            "sources": [
                {"source_name": "polymarket_clob", "freshness_status": "fresh", "priority_level": "critical"},
                {"source_name": "resolver_registry", "freshness_status": "fresh", "priority_level": "high"},
            ],
        },
    )

    assert payload["overall_status"] == "live_ready"
    assert payload["operator"]["can_bot_trade"] is True
    assert payload["operator"]["operator_mode"] == "production_read_only"
    assert payload["block_reasons"] == []
    assert payload["gate_stack"]["resolver_gate"] == "pass"
    assert payload["gate_stack"]["probability_gate"] == "pass"
    assert payload["gate_stack"]["authorization_gate"] == "pass"
    assert payload["validation"]["promotion_state"]["probability_mode"] == "live_approved"
    assert payload["top_parameter_view"]["schema_version"] == "top_parameter_view.v1"


def test_unified_status_builder_includes_source_policy() -> None:
    builder = UnifiedStatusBuilder(now=datetime(2026, 4, 18, 8, 0, tzinfo=timezone.utc))

    payload = builder.build(
        monitoring_report={
            "overall_status": "healthy",
            "counts": {"healthy": 1, "warning": 0, "stale": 0, "missing": 0},
            "workers": [{"label": "Market", "layer": "market_layer", "status": "healthy"}],
        },
        latest_dashboard_rows=[
            {
                "market_id": "m3",
                "market_question": "Will Shanghai exceed 35C?",
                "comparison_status": "aligned",
                "rule_status": "matched",
                "resolver_confidence": 0.9,
                "source_match_grade": "exact_station",
            }
        ],
        probability_shadow_report={
            "states": [
                {
                    "market_id": "m3",
                    "probability_mode": "live_approved",
                    "execution_constraint": "live_execution_allowed",
                    "calibration_status": "calibrated",
                }
            ]
        },
        production_readiness_report={
            "status": "ready",
            "ready_for_live": True,
            "decision": "LIVE_EXECUTION_ALLOWED",
            "blocking_count": 0,
            "warning_count": 0,
        },
        validation_freshness_status={
            "status": "healthy",
            "reason": "validation_report_fresh",
            "freshness_seconds": 300,
        },
        label_coverage_report={
            "status": "healthy",
            "labeled_rows": 300,
            "labeled_ratio": 0.75,
            "blockers": [],
        },
        source_policy_status={
            "schema_version": "source_policy_status.v1",
            "overall_status": "healthy",
            "counts": {"fresh": 3, "stale": 0, "unavailable": 0},
            "priority_counts": {"high": 2},
            "problem_sources": [],
            "sources": [],
        },
    )

    assert payload["source_policy"]["overall_status"] == "healthy"
    assert payload["source_policy"]["fresh_count"] == 3
