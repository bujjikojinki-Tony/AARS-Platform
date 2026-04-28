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


def test_status_api_attaches_family_scan_report(monkeypatch, tmp_path) -> None:
    unified_path = tmp_path / "unified_status.json"
    unified_path.write_text(
        json.dumps(
            {
                "schema_version": "unified_status.v1",
                "overall_status": "guarded",
                "generated_at": "2026-04-21T09:00:00+00:00",
                "current_market": {
                    "market_id": "m-family",
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
                "validation": {
                    "freshness_status": "healthy",
                },
            }
        ),
        encoding="utf-8",
    )
    family_scan_dir = tmp_path / "family_scan_reports"
    family_scan_dir.mkdir()
    family_scan_path = family_scan_dir / "family_scan_20260421.json"
    family_scan_path.write_text(
        json.dumps(
            {
                "schema_version": "family_scan_report.v1",
                "generated_at": "2026-04-21T10:00:00+00:00",
                "input_mode": "canonical_only",
                "family_summaries": [
                    {
                        "market_family": "sea_ice_extent",
                        "max_intervention_like_score": 0.89,
                        "signal_summary": "pv=1 edge=2 mismatch=0 stress=2 peer=1 high=2",
                    }
                ],
                "signal_summary": {
                    "price_velocity_high_count": 1,
                    "edge_dislocation_high_count": 2,
                    "evidence_mismatch_count": 0,
                    "microstructure_stress_high_count": 2,
                    "peer_outlier_count": 1,
                    "intervention_like_high_count": 2,
                },
                "anomaly_bucket_counts": {"high": 1, "medium": 0, "low": 0},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("UNIFIED_STATUS_JSON_PATH", str(unified_path))
    monkeypatch.setenv("FAMILY_SCAN_REPORTS_DIR", str(family_scan_dir))

    payload = StatusAPI().load_latest_status()

    assert payload["latest_family_scan_report"]["schema_version"] == "family_scan_report.v1"
    assert payload["family_anomaly_summary"]["top_family"] == "sea_ice_extent"
    assert payload["family_anomaly_summary"]["top_bucket"] == "high"


def test_status_api_attaches_phase30_validation_and_anomaly(monkeypatch, tmp_path) -> None:
    unified_path = tmp_path / "unified_status.json"
    unified_path.write_text(
        json.dumps(
            {
                "schema_version": "unified_status.v1",
                "overall_status": "guarded",
                "generated_at": "2026-04-22T09:00:00+00:00",
                "current_market": {
                    "market_id": "m-phase30",
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
            }
        ),
        encoding="utf-8",
    )
    validation_dir = tmp_path / "validation"
    anomaly_dir = tmp_path / "anomaly"
    validation_dir.mkdir()
    anomaly_dir.mkdir()
    (validation_dir / "validation_summary_all.json").write_text(
        json.dumps(
            {
                "schema_version": "validation_summary.v1",
                "generated_at": "2026-04-22T10:00:00+00:00",
                "scope_type": "family",
                "scope_id": "all",
                "validation_status": "strong",
                "validation_age": "2h",
                "label_coverage": 0.9,
                "source_coverage": 0.85,
                "normalization_consistency": 1.0,
                "family_support_level": "strong",
                "promotion_readiness": "conditional",
                "reasons": ["fresh labels"],
            }
        ),
        encoding="utf-8",
    )
    (anomaly_dir / "family_anomaly_summary_sea_ice_extent.json").write_text(
        json.dumps(
            {
                "schema_version": "family_anomaly_summary.v1",
                "generated_at": "2026-04-22T10:05:00+00:00",
                "market_family": "sea_ice_extent",
                "scanned_market_count": 2,
                "high_anomaly_count": 1,
                "high_intervention_like_count": 1,
                "family_risk_summary": "moderate_family_anomaly_risk",
                "policy_refs": {"anomaly_policy_ref": "x"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("UNIFIED_STATUS_JSON_PATH", str(unified_path))
    monkeypatch.setenv("VALIDATION_OUTPUT_DIR", str(validation_dir))
    monkeypatch.setenv("ADVANCED_ANOMALY_OUTPUT_DIR", str(anomaly_dir))

    payload = StatusAPI().load_latest_status()

    assert payload["validation_assimilation_summary"]["validation_status"] == "strong"
    assert payload["validation"]["validation_summary_v1"]["promotion_readiness"] == "conditional"
    assert payload["family_anomaly_summary"]["top_family"] == "sea_ice_extent"


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
    assert payload["top_parameter_view"]["schema_version"] == "top_parameter_view.v1"
    assert payload["top_parameter_view"]["market_id"] == "m-api"
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
    assert payload["top_parameter_view"]["schema_version"] == "top_parameter_view.v1"
    assert payload["block_reasons"][0] == "resolver_source_not_exact"
    assert payload["gate_severity"] == "high"
    assert payload["recommended_operator_action"] == "review_resolver_contract"
