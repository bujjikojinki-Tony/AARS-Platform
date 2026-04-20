from pathlib import Path

from weather_dashboard.ui.compact_gate_stack_panel import build_compact_gate_stack_summary


def test_compact_gate_stack_summary_reflects_alignment_and_probability_contract(tmp_path: Path):
    whitelist = tmp_path / "whitelist.yaml"
    whitelist.write_text("markets:\n  - m1\n", encoding="utf-8")

    summary = build_compact_gate_stack_summary(
        market_snapshot={"market_id": "m1", "market_question": "Q1", "favored_side": "yes", "yes_price": 0.61},
        activated_market_snapshot={"market_id": "m1", "updated_at": "2026-04-18T00:00:00+00:00"},
        forecast_snapshot={"market_id": "m1", "timestamp": "2026-04-18T00:00:00+00:00"},
        resolver_rule={"market_id": "m1", "resolver_status": "matched"},
        probability_state={
            "market_id": "m1",
            "probability_mode": "heuristic_not_calibrated",
            "execution_constraint": "manual_advisory_only",
        },
        comparison_row={"market_id": "m1", "comparison_status": "aligned"},
        validation_freshness_status={"status": "healthy"},
        label_coverage_report={"status": "healthy"},
        bot_authorized=True,
        whitelist_path=whitelist,
    )

    assert summary["selected_market_id"] == "m1"
    assert summary["alignment_ok"] >= 5
    assert summary["probability_mode"] == "heuristic_not_calibrated"
    assert summary["resolver_gate"] == "blocked"
    assert "resolver_confidence_low" in summary["resolver_gate_reasons"]
    assert summary["execution_constraint"] == "manual_advisory_only"
    assert summary["validation_freshness_status"] == "healthy"
    assert summary["label_coverage_status"] == "healthy"
    assert summary["gate_status"] == "READY"


def test_compact_gate_stack_uses_unified_fallback_when_api_missing(tmp_path: Path):
    whitelist = tmp_path / "whitelist.yaml"
    whitelist.write_text("markets:\n  - m1\n", encoding="utf-8")

    summary = build_compact_gate_stack_summary(
        market_snapshot={"market_id": "m1", "market_question": "Q1", "favored_side": "yes", "yes_price": 0.61},
        activated_market_snapshot={"market_id": "m1", "updated_at": "2026-04-18T00:00:00+00:00"},
        forecast_snapshot={"market_id": "m1", "timestamp": "2026-04-18T00:00:00+00:00"},
        resolver_rule={"market_id": "m1", "resolver_status": "matched", "resolver_confidence": 0.95, "source_match_grade": "exact_station"},
        probability_state={
            "market_id": "m1",
            "probability_mode": "live_approved",
            "execution_constraint": "live_execution_allowed",
        },
        comparison_row={"market_id": "m1", "comparison_status": "aligned"},
        validation_freshness_status={"status": "healthy"},
        label_coverage_report={"status": "healthy"},
        unified_status_report={
            "current_market": {"market_id": "m1"},
            "gate_stack": {
                "resolver_gate": "blocked",
                "resolver_gate_reasons": ["resolver_source_not_exact"],
                "probability_gate": "blocked",
                "freshness_gate": "pass",
                "execution_gate": "blocked",
                "block_reasons": ["resolver_source_not_exact", "probability_not_live_approved"],
            },
        },
        bot_authorized=True,
        whitelist_path=whitelist,
    )

    assert summary["resolver_gate"] == "blocked"
    assert summary["probability_gate"] == "blocked"
    assert summary["execution_gate"] == "blocked"
    assert "probability_not_live_approved" in summary["blockers"]
    assert summary["gate_source"] == "unified_fallback"


def test_compact_gate_stack_uses_gate_stack_api_market_view_when_unified_missing(tmp_path: Path):
    whitelist = tmp_path / "whitelist.yaml"
    whitelist.write_text("markets:\n  - m9\n", encoding="utf-8")

    summary = build_compact_gate_stack_summary(
        market_snapshot={"market_id": "m9", "market_question": "Q9", "favored_side": "yes", "yes_price": 0.61},
        activated_market_snapshot={"market_id": "m9", "updated_at": "2026-04-18T00:00:00+00:00"},
        forecast_snapshot={"market_id": "m9", "timestamp": "2026-04-18T00:00:00+00:00"},
        resolver_rule={"market_id": "m9", "resolver_status": "matched", "resolver_confidence": 0.95, "source_match_grade": "exact_station"},
        probability_state={
            "market_id": "m9",
            "probability_mode": "live_approved",
            "execution_constraint": "live_execution_allowed",
        },
        comparison_row={"market_id": "m9", "comparison_status": "aligned"},
        validation_freshness_status={"status": "healthy"},
        label_coverage_report={"status": "healthy"},
        gate_stack_api_report={
            "schema_version": "gate_stack_api.v1",
            "severity": "medium",
            "recommended_operator_action": "hold_execution_and_review",
            "market_gate_views": [
                {
                    "market_id": "m9",
                    "resolver_gate": "blocked",
                    "resolver_gate_reasons": ["resolver_source_not_exact"],
                    "probability_gate": "blocked",
                    "freshness_gate": "pass",
                    "authorization_gate": "blocked",
                    "execution_gate": "blocked",
                    "block_reasons": ["resolver_source_not_exact", "execution_not_ready"],
                    "severity": "high",
                    "recommended_operator_action": "review_resolver_contract",
                }
            ],
        },
        bot_authorized=True,
        whitelist_path=whitelist,
    )

    assert summary["resolver_gate"] == "blocked"
    assert summary["execution_gate"] == "blocked"
    assert summary["gate_source"] == "api"
    assert summary["severity"] == "high"
    assert summary["recommended_operator_action"] == "review_resolver_contract"


def test_compact_gate_stack_prefers_api_over_unified_fallback(tmp_path: Path):
    whitelist = tmp_path / "whitelist.yaml"
    whitelist.write_text("markets:\n  - m2\n", encoding="utf-8")

    summary = build_compact_gate_stack_summary(
        market_snapshot={"market_id": "m2", "market_question": "Q2", "favored_side": "yes", "yes_price": 0.61},
        activated_market_snapshot={"market_id": "m2", "updated_at": "2026-04-18T00:00:00+00:00"},
        forecast_snapshot={"market_id": "m2", "timestamp": "2026-04-18T00:00:00+00:00"},
        resolver_rule={"market_id": "m2", "resolver_status": "matched", "resolver_confidence": 0.95, "source_match_grade": "exact_station"},
        probability_state={
            "market_id": "m2",
            "probability_mode": "live_approved",
            "execution_constraint": "live_execution_allowed",
        },
        comparison_row={"market_id": "m2", "comparison_status": "aligned"},
        validation_freshness_status={"status": "healthy"},
        label_coverage_report={"status": "healthy"},
        unified_status_report={
            "current_market": {"market_id": "m2"},
            "gate_stack": {
                "resolver_gate": "pass",
                "probability_gate": "pass",
                "freshness_gate": "pass",
                "authorization_gate": "pass",
                "execution_gate": "pass",
                "block_reasons": [],
            },
        },
        gate_stack_api_report={
            "schema_version": "gate_stack_api.v1",
            "market_gate_views": [
                {
                    "market_id": "m2",
                    "resolver_gate": "blocked",
                    "resolver_gate_reasons": ["resolver_source_not_exact"],
                    "probability_gate": "blocked",
                    "freshness_gate": "pass",
                    "authorization_gate": "blocked",
                    "execution_gate": "blocked",
                    "block_reasons": ["resolver_source_not_exact"],
                    "severity": "high",
                    "recommended_operator_action": "review_resolver_contract",
                }
            ],
        },
        bot_authorized=True,
        whitelist_path=whitelist,
    )

    assert summary["gate_source"] == "api"
    assert summary["resolver_gate"] == "blocked"
    assert "resolver_source_not_exact" in summary["blockers"]
