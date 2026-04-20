from __future__ import annotations

import json

from weather_telegram_console.integrations.status_api import StatusAPI


def test_status_api_adds_gate_stack_when_unified_missing_gate_stack(monkeypatch, tmp_path) -> None:
    unified_path = tmp_path / "unified_status.json"
    unified_path.write_text(
        json.dumps(
            {
                "schema_version": "unified_status.v1",
                "overall_status": "guarded",
                "generated_at": "2026-04-18T09:00:00+00:00",
                "current_market": {
                    "market_id": "m1",
                    "comparison_status": "aligned",
                    "rule_status": "matched",
                },
                "monitoring": {
                    "overall_status": "healthy",
                    "workers": [{"label": "Market", "status": "healthy"}],
                },
                "probability": {
                    "probability_mode": "heuristic_not_calibrated",
                    "execution_constraint": "manual_advisory_only",
                    "calibration_status": "not_calibrated",
                },
                "execution": {
                    "status": "blocked",
                    "ready_for_live": False,
                },
                "block_reasons": ["execution:blocked"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("UNIFIED_STATUS_JSON_PATH", str(unified_path))
    payload = StatusAPI().load_latest_status()

    assert isinstance(payload.get("gate_stack"), dict)
    assert payload["gate_stack"]["authorization_gate"] == "blocked"
    assert payload["gate_stack"]["execution_gate"] == "blocked"


def test_status_api_can_read_gate_stack_api_without_unified(monkeypatch, tmp_path) -> None:
    gate_stack_api_path = tmp_path / "gate_stack_api.json"
    gate_stack_api_path.write_text(
        json.dumps(
            {
                "schema_version": "gate_stack_api.v1",
                "generated_at": "2026-04-19T09:00:00+00:00",
                "source_schema_version": "unified_status.v1",
                "overall_status": "guarded",
                "market_id": "m-api",
                "gate_stack": {
                    "data_gate": "pass",
                    "data_gate_reasons": [],
                    "resolver_gate": "blocked",
                    "resolver_gate_reasons": ["resolver_not_matched"],
                    "probability_gate": "blocked",
                    "probability_gate_reasons": ["probability_not_live_approved"],
                    "freshness_gate": "pass",
                    "freshness_gate_reasons": [],
                    "authorization_gate": "blocked",
                    "authorization_gate_reasons": [
                        "resolver_not_matched",
                        "probability_not_live_approved",
                    ],
                    "execution_gate": "blocked",
                    "execution_gate_reasons": ["execution_not_ready"],
                    "block_reasons": [
                        "resolver_not_matched",
                        "probability_not_live_approved",
                        "execution_not_ready",
                    ],
                },
                "block_reasons": [
                    "resolver_not_matched",
                    "probability_not_live_approved",
                    "execution_not_ready",
                ],
                "promotion_state": {
                    "schema_version": "promotion_state.v1",
                    "probability_mode": "shadow_calibrated_candidate",
                    "base_probability_mode": "heuristic_not_calibrated",
                    "execution_constraint": "dry_run_only",
                    "base_execution_constraint": "manual_advisory_only",
                    "promotion_reason": "candidate_thresholds_passed",
                    "demotion_reason": None,
                },
                "can_execute": False,
                "primary_block_reason": "resolver_not_matched",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("UNIFIED_STATUS_JSON_PATH", str(tmp_path / "missing_unified_status.json"))
    monkeypatch.setenv("GATE_STACK_API_JSON_PATH", str(gate_stack_api_path))

    payload = StatusAPI().load_latest_status()

    assert payload["current_market"]["market_id"] == "m-api"
    assert payload["contracts"]["gate_stack_api_version"] == "gate_stack_api.v1"
    assert payload["promotion_state"]["probability_mode"] == "shadow_calibrated_candidate"
    assert payload["gate_stack"]["resolver_gate"] == "blocked"
    assert payload["block_reasons"][0] == "resolver_not_matched"
    assert payload["gate_severity"] == "medium"
    assert payload["recommended_operator_action"] == "review_resolver_contract"


def test_status_api_prefers_market_view_from_gate_stack_api(monkeypatch, tmp_path) -> None:
    unified_path = tmp_path / "unified_status.json"
    unified_path.write_text(
        json.dumps(
            {
                "schema_version": "unified_status.v1",
                "overall_status": "guarded",
                "generated_at": "2026-04-18T09:00:00+00:00",
                "current_market": {"market_id": "m-target", "comparison_status": "aligned", "rule_status": "matched"},
                "monitoring": {"overall_status": "healthy", "workers": [{"label": "Market", "status": "healthy"}]},
                "probability": {
                    "probability_mode": "heuristic_not_calibrated",
                    "execution_constraint": "manual_advisory_only",
                    "calibration_status": "not_calibrated",
                    "promotion_state": {
                        "schema_version": "promotion_state.v1",
                        "probability_mode": "heuristic_not_calibrated",
                        "base_probability_mode": "heuristic_not_calibrated",
                        "execution_constraint": "manual_advisory_only",
                        "base_execution_constraint": "manual_advisory_only",
                        "promotion_reason": "thresholds_not_met",
                        "demotion_reason": "validation_freshness_unhealthy",
                    },
                },
                "execution": {"status": "blocked", "ready_for_live": False},
                "gate_stack": {"resolver_gate": "pass", "block_reasons": []},
            }
        ),
        encoding="utf-8",
    )
    gate_stack_api_path = tmp_path / "gate_stack_api.json"
    gate_stack_api_path.write_text(
        json.dumps(
            {
                "schema_version": "gate_stack_api.v1",
                "market_gate_views": [
                    {
                        "market_id": "m-target",
                        "resolver_gate": "blocked",
                        "resolver_gate_reasons": ["resolver_source_not_exact"],
                        "probability_gate": "blocked",
                        "probability_gate_reasons": ["probability_not_live_approved"],
                        "freshness_gate": "pass",
                        "freshness_gate_reasons": [],
                        "authorization_gate": "blocked",
                        "authorization_gate_reasons": ["resolver_source_not_exact"],
                        "execution_gate": "blocked",
                        "execution_gate_reasons": ["execution_not_ready"],
                        "block_reasons": ["resolver_source_not_exact", "execution_not_ready"],
                        "severity": "high",
                        "recommended_operator_action": "review_resolver_contract",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("UNIFIED_STATUS_JSON_PATH", str(unified_path))
    monkeypatch.setenv("GATE_STACK_API_JSON_PATH", str(gate_stack_api_path))

    payload = StatusAPI().load_latest_status()

    assert payload["gate_stack"]["resolver_gate"] == "blocked"
    assert payload["promotion_state"]["demotion_reason"] == "validation_freshness_unhealthy"
    assert payload["block_reasons"][0] == "resolver_source_not_exact"
    assert payload["gate_severity"] == "high"
    assert payload["recommended_operator_action"] == "review_resolver_contract"
