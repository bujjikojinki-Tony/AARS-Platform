from __future__ import annotations

import json

from typer.testing import CliRunner

from weather_comparison_engine import main as comparison_main
from weather_comparison_engine.status import GateStackAPIBuilder


def test_gate_stack_api_builder_normalizes_gate_stack() -> None:
    payload = GateStackAPIBuilder().build(
        {
            "schema_version": "unified_status.v1",
            "generated_at": "2026-04-19T09:00:00+00:00",
            "overall_status": "guarded",
            "current_market": {"market_id": "m-123"},
            "gate_stack": {
                "resolver_gate": "blocked",
                "resolver_gate_reasons": ["resolver_not_matched"],
            },
        }
    )

    assert payload["schema_version"] == "gate_stack_api.v1"
    assert payload["source_schema_version"] == "unified_status.v1"
    assert payload["market_id"] == "m-123"
    assert payload["gate_stack"]["resolver_gate"] == "blocked"
    assert payload["gate_stack"]["probability_gate"] == "blocked"
    assert payload["block_reasons"] == ["resolver_not_matched"]
    assert payload["can_execute"] is False
    assert payload["primary_block_reason"] == "resolver_not_matched"
    assert payload["severity"] == "medium"
    assert payload["recommended_operator_action"] == "review_resolver_contract"


def test_gate_stack_api_builder_emits_market_gate_views() -> None:
    payload = GateStackAPIBuilder().build(
        {
            "schema_version": "unified_status.v1",
            "generated_at": "2026-04-19T09:00:00+00:00",
            "overall_status": "warning",
            "current_market": {"market_id": "m-1"},
            "gate_stack": {
                "probability_gate": "blocked",
                "probability_gate_reasons": ["probability_not_live_approved"],
                "freshness_gate": "pass",
                "freshness_gate_reasons": [],
                "execution_gate": "blocked",
                "execution_gate_reasons": ["execution_not_ready"],
                "authorization_gate": "blocked",
                "authorization_gate_reasons": ["probability_not_live_approved"],
            },
        },
        latest_dashboard_rows=[
            {
                "market_id": "m-1",
                "market_question": "Q1",
                "comparison_status": "aligned",
                "rule_status": "matched",
                "resolver_confidence": 0.9,
                "source_match_grade": "exact_station",
            },
            {
                "market_id": "m-2",
                "market_question": "Q2",
                "comparison_status": "market_mismatch",
                "rule_status": "unmatched",
                "resolver_confidence": 0.2,
                "source_match_grade": "family_only",
            },
        ],
    )

    assert payload["market_count"] == 2
    m1 = payload["market_gate_views"][0]
    m2 = payload["market_gate_views"][1]
    assert m1["market_id"] == "m-1"
    assert m1["resolver_gate"] == "pass"
    assert m1["probability_gate"] == "blocked"
    assert m2["market_id"] == "m-2"
    assert m2["resolver_gate"] == "blocked"
    assert "resolver_not_matched" in m2["resolver_gate_reasons"]
    assert m2["severity"] == "medium"
    assert m2["recommended_operator_action"] == "review_resolver_contract"


def test_build_unified_status_cli_also_writes_gate_stack_api(monkeypatch, tmp_path) -> None:
    monitoring_path = tmp_path / "monitoring_status.json"
    latest_rows_path = tmp_path / "latest_dashboard_rows.json"
    probability_path = tmp_path / "probability_shadow_report.json"
    readiness_path = tmp_path / "production_readiness_report.json"
    validation_freshness_path = tmp_path / "validation_freshness_status.json"
    coverage_path = tmp_path / "label_coverage_report.json"
    source_policy_path = tmp_path / "source_policy_status.json"
    unified_out = tmp_path / "unified_status.json"
    gate_out = tmp_path / "gate_stack_api.json"

    monitoring_path.write_text(
        json.dumps(
            {
                "overall_status": "healthy",
                "workers": [{"label": "Market", "status": "healthy"}],
                "counts": {"healthy": 1, "warning": 0, "stale": 0, "missing": 0},
            }
        ),
        encoding="utf-8",
    )
    latest_rows_path.write_text(
        json.dumps(
            [
                {
                    "market_id": "m-200",
                    "comparison_status": "aligned",
                    "rule_status": "matched",
                    "resolver_confidence": 0.95,
                    "source_match_grade": "exact_station",
                }
            ]
        ),
        encoding="utf-8",
    )
    probability_path.write_text(
        json.dumps(
            {
                "states": [
                    {
                        "market_id": "m-200",
                        "probability_mode": "live_approved",
                        "execution_constraint": "live_execution_allowed",
                        "calibration_status": "calibrated",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    readiness_path.write_text(
        json.dumps(
            {
                "status": "ready",
                "ready_for_live": True,
                "decision": "LIVE_EXECUTION_ALLOWED",
                "blocking_count": 0,
                "warning_count": 0,
            }
        ),
        encoding="utf-8",
    )
    validation_freshness_path.write_text(
        json.dumps({"status": "healthy", "freshness_seconds": 10}),
        encoding="utf-8",
    )
    coverage_path.write_text(
        json.dumps({"status": "healthy", "labeled_rows": 100, "labeled_ratio": 0.8}),
        encoding="utf-8",
    )
    source_policy_path.write_text(
        json.dumps(
            {
                "schema_version": "source_policy_status.v1",
                "generated_at": "2026-04-19T09:00:00+00:00",
                "registry_schema_version": "source_policy_registry.v1",
                "overall_status": "healthy",
                "counts": {"fresh": 4, "stale": 0, "unavailable": 0},
                "priority_counts": {"critical": 1, "high": 2, "medium": 1},
                "problem_sources": [],
                "sources": [
                    {"source_name": "polymarket_clob", "freshness_status": "fresh", "priority_level": "critical"}
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(comparison_main, "MONITORING_STATUS_JSON", monitoring_path)
    monkeypatch.setattr(comparison_main, "LATEST_DASHBOARD_ROWS_JSON", latest_rows_path)
    monkeypatch.setattr(comparison_main, "PROBABILITY_SHADOW_REPORT_JSON", probability_path)
    monkeypatch.setattr(comparison_main, "EXECUTION_GATEWAY_PRODUCTION_READINESS_JSON", readiness_path)
    monkeypatch.setattr(comparison_main, "VALIDATION_FRESHNESS_STATUS_JSON", validation_freshness_path)
    monkeypatch.setattr(comparison_main, "LABEL_COVERAGE_REPORT_JSON", coverage_path)
    monkeypatch.setattr(comparison_main, "SOURCE_POLICY_STATUS_JSON", source_policy_path)
    monkeypatch.setattr(
        comparison_main,
        "_write_source_policy_status",
        lambda: source_policy_path,
    )
    monkeypatch.setattr(comparison_main, "UNIFIED_STATUS_JSON", unified_out)
    monkeypatch.setattr(comparison_main, "GATE_STACK_API_JSON", gate_out)

    result = CliRunner().invoke(comparison_main.app, ["build-unified-status"])

    assert result.exit_code == 0
    assert unified_out.exists()
    assert gate_out.exists()
    gate_payload = json.loads(gate_out.read_text(encoding="utf-8"))
    assert gate_payload["schema_version"] == "gate_stack_api.v1"
    assert gate_payload["market_id"] == "m-200"
    assert gate_payload["gate_stack"]["execution_gate"] == "pass"
    assert gate_payload["market_count"] == 1
    assert gate_payload["market_gate_views"][0]["market_id"] == "m-200"
    assert gate_payload["recommended_operator_action"] == "allow_live_execution"
    assert gate_payload["source_policy"]["schema_version"] == "source_policy_status.v1"
