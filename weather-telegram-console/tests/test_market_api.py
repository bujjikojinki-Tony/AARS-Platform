from __future__ import annotations

import json

from weather_telegram_console.integrations.market_api import MarketAPI


def test_market_api_load_market_summary(monkeypatch, tmp_path) -> None:
    dashboard_rows = tmp_path / "latest_dashboard_rows.json"
    dashboard_rows.write_text(
        json.dumps(
            [
                {
                    "market_id": "mkt_123",
                    "market_question": "Will NYC hit 95F?",
                    "comparison_status": "aligned",
                    "market_snapshot_ref": "2026-04-18T09:00:00+00:00",
                    "forecast_snapshot_ref": "2026-04-18T09:05:00+00:00",
                }
            ]
        ),
        encoding="utf-8",
    )
    audit_path = tmp_path / "manual_advisory_audit.jsonl"
    audit_path.write_text(
        json.dumps(
            {
                "market_id": "mkt_123",
                "created_at": "2026-04-18T09:10:00+00:00",
                "event_type": "operator_acknowledged_manual_advisory",
                "payload": {
                    "approval_status": "operator_acknowledged",
                    "manual_trade_ticket": {"price": 0.44, "size": 12},
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("LATEST_DASHBOARD_ROWS_JSON_PATH", str(dashboard_rows))
    monkeypatch.setenv("MANUAL_ADVISORY_AUDIT_JSONL", str(audit_path))
    monkeypatch.setenv("OPERATOR_MARKET_CONTEXT_JSON", str(tmp_path / "missing_operator_context.json"))
    monkeypatch.setenv("GATE_STACK_API_JSON_PATH", str(tmp_path / "missing_gate_stack_api.json"))

    payload = MarketAPI().load_market_summary("mkt_123")

    assert payload["market_id"] == "mkt_123"
    assert payload["comparison_status"] == "aligned"
    assert payload["advisory_summary"]["event_count"] == 1
    assert payload["data_availability"]["market_snapshot_ref_present"] is True
    assert payload["compact_gate_stack"]["resolver_gate"] == "blocked"
    assert "resolver_confidence_low" in payload["compact_gate_stack"]["resolver_gate_reasons"]
    assert isinstance(payload["promotion_state"], dict)
    assert "probability_mode" in payload["promotion_state"] or "approved_for_live" in payload["promotion_state"]
    assert payload["top_parameter_view"]["schema_version"] == "top_parameter_view.v1"


def test_market_api_load_market_summary_includes_workstation_context(monkeypatch, tmp_path) -> None:
    dashboard_rows = tmp_path / "latest_dashboard_rows.json"
    dashboard_rows.write_text(
        json.dumps(
            [
                {
                    "market_id": "mkt_123",
                    "market_question": "Will NYC hit 95F?",
                    "market_family": "temperature_daily_max",
                    "location_name": "New York",
                    "comparison_status": "aligned",
                    "resolver_status": "matched",
                    "resolver_confidence": 0.95,
                    "source_match_grade": "exact_station",
                }
            ]
        ),
        encoding="utf-8",
    )
    alert_dir = tmp_path / "alerts"
    anomaly_dir = tmp_path / "anomalies"
    family_dir = tmp_path / "family_scan_reports"
    alert_dir.mkdir()
    anomaly_dir.mkdir()
    family_dir.mkdir()
    (alert_dir / "alert.json").write_text(
        json.dumps(
            {
                "market_id": "mkt_123",
                "severity": "amber",
                "primary_reason": "forecast_divergence",
            }
        ),
        encoding="utf-8",
    )
    (anomaly_dir / "anomaly.jsonl").write_text(
        json.dumps(
            {
                "market_id": "mkt_123",
                "anomaly_score": 0.71,
                "anomaly_bucket": "medium",
                "primary_reason": "edge_dislocation",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (family_dir / "family_scan.json").write_text(
        json.dumps(
            {
                "schema_version": "family_scan_report.v1",
                "generated_at": "2026-04-22T03:00:00+00:00",
                "input_mode": "canonical_only",
                "family_summaries": [
                    {
                        "market_family": "sea_ice_extent",
                        "max_intervention_like_score": 0.91,
                        "signal_summary": "pv=1 edge=1 mismatch=0 stress=2 peer=1 high=2",
                    }
                ],
                "signal_summary": {
                    "price_velocity_high_count": 1,
                    "edge_dislocation_high_count": 1,
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
    opportunity_board = tmp_path / "opportunity_board_view.json"
    opportunity_board.write_text(
        json.dumps(
            {
                "schema_version": "opportunity_board_view.v1",
                "rows": [
                    {
                        "row_id": "New York.temperature_daily_max",
                        "city": "New York",
                        "market_family": "temperature_daily_max",
                        "opportunity_score": 0.82,
                        "difficulty_label": "medium",
                        "recommended_action": "open_workstation",
                        "best_model": "NOAA",
                        "best_source_stack": ["hrrr", "metar", "official_obs"],
                        "upstream_refs": {"market_ids": ["mkt_123"]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    model_validation = tmp_path / "model_validation_report.json"
    model_validation.write_text(
        json.dumps(
            {
                "sample_count": 40,
                "labeled_sample_count": 4,
                "calibration_status": "not_calibrated",
                "promotion_state": {"probability_mode": "shadow_calibrated_candidate"},
            }
        ),
        encoding="utf-8",
    )
    freshness = tmp_path / "validation_freshness_status.json"
    freshness.write_text(json.dumps({"status": "blocked", "reason": "validation_report_stale"}), encoding="utf-8")
    coverage = tmp_path / "label_coverage_report.json"
    coverage.write_text(json.dumps({"status": "blocked", "labeled_ratio": 0.1}), encoding="utf-8")

    monkeypatch.setenv("LATEST_DASHBOARD_ROWS_JSON_PATH", str(dashboard_rows))
    monkeypatch.setenv("MARKET_ALERT_EVENTS_DIR", str(alert_dir))
    monkeypatch.setenv("MARKET_ANOMALY_EVENTS_DIR", str(anomaly_dir))
    monkeypatch.setenv("FAMILY_SCAN_REPORTS_DIR", str(family_dir))
    monkeypatch.setenv("OPPORTUNITY_BOARD_VIEW_JSON_PATH", str(opportunity_board))
    monkeypatch.setenv("MODEL_VALIDATION_REPORT_JSON", str(model_validation))
    monkeypatch.setenv("VALIDATION_FRESHNESS_STATUS_JSON", str(freshness))
    monkeypatch.setenv("LABEL_COVERAGE_REPORT_JSON", str(coverage))
    monkeypatch.setenv("MANUAL_ADVISORY_AUDIT_JSONL", str(tmp_path / "missing_audit.jsonl"))
    monkeypatch.setenv("OPERATOR_MARKET_CONTEXT_JSON", str(tmp_path / "missing_operator_context.json"))
    monkeypatch.setenv("GATE_STACK_API_JSON_PATH", str(tmp_path / "missing_gate_stack_api.json"))

    payload = MarketAPI().load_market_summary("mkt_123")

    workstation = payload["workstation_context"]
    assert workstation["schema_version"] == "telegram_market_workstation_context.v1"
    assert workstation["market_alert"]["primary_reason"] == "forecast_divergence"
    assert workstation["family_anomaly"]["primary_reason"] == "edge_dislocation"
    assert workstation["family_anomaly_summary"]["top_family"] == "sea_ice_extent"
    assert workstation["gate_summary"]["execution_boundary"] == "gate_stack_api.v1_only"
    assert workstation["validation_summary"]["freshness_status"] == "blocked"
    assert workstation["opportunity_entry"]["recommended_action"] == "open_workstation"
    assert payload["family_anomaly_summary"]["top_bucket"] == "high"


def test_market_api_prefers_phase30_validation_and_anomaly_artifacts(monkeypatch, tmp_path) -> None:
    dashboard_rows = tmp_path / "latest_dashboard_rows.json"
    dashboard_rows.write_text(
        json.dumps(
            [
                {
                    "market_id": "mkt_phase30",
                    "market_question": "Will NYC hit 95F?",
                    "market_family": "temperature_daily_max",
                    "location_name": "New York",
                    "comparison_status": "aligned",
                    "resolver_status": "matched",
                    "resolver_confidence": 0.95,
                    "source_match_grade": "exact_station",
                }
            ]
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
                "generated_at": "2026-04-22T11:00:00+00:00",
                "scope_type": "family",
                "scope_id": "all",
                "validation_status": "moderate",
                "validation_age": "3h",
                "label_coverage": 0.8,
                "source_coverage": 0.75,
                "normalization_consistency": 1.0,
                "family_support_level": "moderate",
                "promotion_readiness": "conditional",
                "reasons": ["some labels"],
            }
        ),
        encoding="utf-8",
    )
    (anomaly_dir / "family_anomaly_summary_sea_ice_extent.json").write_text(
        json.dumps(
            {
                "schema_version": "family_anomaly_summary.v1",
                "generated_at": "2026-04-22T11:05:00+00:00",
                "market_family": "sea_ice_extent",
                "scanned_market_count": 2,
                "high_anomaly_count": 1,
                "high_intervention_like_count": 1,
                "family_risk_summary": "moderate_family_anomaly_risk",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LATEST_DASHBOARD_ROWS_JSON_PATH", str(dashboard_rows))
    monkeypatch.setenv("VALIDATION_OUTPUT_DIR", str(validation_dir))
    monkeypatch.setenv("ADVANCED_ANOMALY_OUTPUT_DIR", str(anomaly_dir))
    monkeypatch.setenv("FAMILY_SCAN_REPORTS_DIR", str(tmp_path / "missing_family_scan_reports"))
    monkeypatch.setenv("MANUAL_ADVISORY_AUDIT_JSONL", str(tmp_path / "missing_audit.jsonl"))
    monkeypatch.setenv("OPERATOR_MARKET_CONTEXT_JSON", str(tmp_path / "missing_operator_context.json"))
    monkeypatch.setenv("GATE_STACK_API_JSON_PATH", str(tmp_path / "missing_gate_stack_api.json"))

    payload = MarketAPI().load_market_summary("mkt_phase30")

    assert payload["validation_summary_v1"]["validation_status"] == "moderate"
    assert payload["workstation_context"]["validation_summary_v1"]["promotion_readiness"] == "conditional"
    assert payload["family_anomaly_summary"]["top_family"] == "sea_ice_extent"


def test_market_api_load_market_timeline_uses_unified_current_market(monkeypatch, tmp_path) -> None:
    history_path = tmp_path / "comparison_history.json"
    history_path.write_text(
        json.dumps(
            [
                {
                    "market_id": "mkt_123",
                    "timestamp": "2026-04-18T09:00:00+00:00",
                    "comparison_status": "aligned",
                },
                {
                    "market_id": "mkt_123",
                    "timestamp": "2026-04-18T08:00:00+00:00",
                    "comparison_status": "edge_yes",
                },
                {
                    "market_id": "mkt_other",
                    "timestamp": "2026-04-18T10:00:00+00:00",
                    "comparison_status": "watch",
                },
            ]
        ),
        encoding="utf-8",
    )
    unified_status = tmp_path / "unified_status.json"
    unified_status.write_text(
        json.dumps({"current_market": {"market_id": "mkt_123"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("COMPARISON_HISTORY_JSON_PATH", str(history_path))
    monkeypatch.setenv("UNIFIED_STATUS_JSON_PATH", str(unified_status))
    monkeypatch.setenv("OPERATOR_MARKET_CONTEXT_JSON", str(tmp_path / "missing_operator_context.json"))

    entries = MarketAPI().load_market_timeline()

    assert len(entries) == 2
    assert entries[0]["timestamp"] == "2026-04-18T09:00:00+00:00"
    assert all(entry["market_id"] == "mkt_123" for entry in entries)


def test_market_api_load_market_timeline_prefers_operator_market_context(monkeypatch, tmp_path) -> None:
    history_path = tmp_path / "comparison_history.json"
    history_path.write_text(
        json.dumps(
            [
                {
                    "market_id": "mkt_operator",
                    "timestamp": "2026-04-18T09:00:00+00:00",
                    "comparison_status": "aligned",
                },
                {
                    "market_id": "mkt_unified",
                    "timestamp": "2026-04-18T10:00:00+00:00",
                    "comparison_status": "edge_yes",
                },
            ]
        ),
        encoding="utf-8",
    )
    unified_status = tmp_path / "unified_status.json"
    unified_status.write_text(
        json.dumps({"current_market": {"market_id": "mkt_unified"}}),
        encoding="utf-8",
    )
    operator_context = tmp_path / "operator_market_context.json"
    operator_context.write_text(
        json.dumps({"market_id": "mkt_operator", "selection_source": "watchlist"}),
        encoding="utf-8",
    )
    monkeypatch.setenv("COMPARISON_HISTORY_JSON_PATH", str(history_path))
    monkeypatch.setenv("UNIFIED_STATUS_JSON_PATH", str(unified_status))
    monkeypatch.setenv("OPERATOR_MARKET_CONTEXT_JSON", str(operator_context))

    entries = MarketAPI().load_market_timeline()

    assert len(entries) == 1
    assert entries[0]["market_id"] == "mkt_operator"


def test_market_api_market_summary_uses_unified_fallback_when_api_missing(monkeypatch, tmp_path) -> None:
    dashboard_rows = tmp_path / "latest_dashboard_rows.json"
    dashboard_rows.write_text(
        json.dumps(
            [
                {
                    "market_id": "mkt_123",
                    "market_question": "Will NYC hit 95F?",
                    "resolver_status": "matched",
                    "resolver_confidence": 0.95,
                    "source_match_grade": "exact_station",
                    "promotion_state": {
                        "schema_version": "promotion_state.v1",
                        "probability_mode": "shadow_calibrated_candidate",
                        "base_probability_mode": "heuristic_not_calibrated",
                        "execution_constraint": "dry_run_only",
                        "base_execution_constraint": "manual_advisory_only",
                        "promotion_reason": "candidate_thresholds_passed",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )
    unified_status = tmp_path / "unified_status.json"
    unified_status.write_text(
        json.dumps(
            {
                "current_market": {"market_id": "mkt_123"},
                "gate_stack": {
                    "resolver_gate": "blocked",
                    "resolver_gate_reasons": ["resolver_source_not_exact"],
                    "probability_gate": "blocked",
                    "freshness_gate": "pass",
                    "execution_gate": "blocked",
                    "block_reasons": ["resolver_source_not_exact"],
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LATEST_DASHBOARD_ROWS_JSON_PATH", str(dashboard_rows))
    monkeypatch.setenv("UNIFIED_STATUS_JSON_PATH", str(unified_status))
    monkeypatch.setenv("MANUAL_ADVISORY_AUDIT_JSONL", str(tmp_path / "missing_audit.jsonl"))
    monkeypatch.setenv("OPERATOR_MARKET_CONTEXT_JSON", str(tmp_path / "missing_operator_context.json"))
    monkeypatch.setenv("GATE_STACK_API_JSON_PATH", str(tmp_path / "missing_gate_stack_api.json"))

    payload = MarketAPI().load_market_summary("mkt_123")

    assert payload["compact_gate_stack"]["source"] == "unified_fallback"
    assert payload["compact_gate_stack"]["resolver_gate"] == "blocked"
    assert "resolver_source_not_exact" in payload["compact_gate_stack"]["resolver_gate_reasons"]
    assert payload["promotion_state"]["probability_mode"] == "shadow_calibrated_candidate"
    assert payload["top_parameter_view"]["schema_version"] == "top_parameter_view.v1"


def test_market_api_market_summary_prefers_api_over_unified(monkeypatch, tmp_path) -> None:
    dashboard_rows = tmp_path / "latest_dashboard_rows.json"
    dashboard_rows.write_text(
        json.dumps(
            [
                {
                    "market_id": "mkt_777",
                    "market_question": "Will NYC hit 95F?",
                    "resolver_status": "matched",
                    "resolver_confidence": 0.95,
                    "source_match_grade": "exact_station",
                    "promotion_state": {
                        "schema_version": "promotion_state.v1",
                        "probability_mode": "heuristic_not_calibrated",
                        "base_probability_mode": "heuristic_not_calibrated",
                        "execution_constraint": "manual_advisory_only",
                        "base_execution_constraint": "manual_advisory_only",
                        "promotion_reason": "thresholds_not_met",
                        "demotion_reason": "validation_freshness_unhealthy",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )
    unified_status = tmp_path / "unified_status.json"
    unified_status.write_text(
        json.dumps(
            {
                "current_market": {"market_id": "mkt_777"},
                "gate_stack": {
                    "resolver_gate": "pass",
                    "probability_gate": "pass",
                    "freshness_gate": "pass",
                    "authorization_gate": "pass",
                    "execution_gate": "pass",
                    "block_reasons": [],
                },
            }
        ),
        encoding="utf-8",
    )
    gate_stack_api = tmp_path / "gate_stack_api.json"
    gate_stack_api.write_text(
        json.dumps(
            {
                "schema_version": "gate_stack_api.v1",
                "market_gate_views": [
                    {
                        "market_id": "mkt_777",
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
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LATEST_DASHBOARD_ROWS_JSON_PATH", str(dashboard_rows))
    monkeypatch.setenv("UNIFIED_STATUS_JSON_PATH", str(unified_status))
    monkeypatch.setenv("GATE_STACK_API_JSON_PATH", str(gate_stack_api))
    monkeypatch.setenv("MANUAL_ADVISORY_AUDIT_JSONL", str(tmp_path / "missing_audit.jsonl"))
    monkeypatch.setenv("OPERATOR_MARKET_CONTEXT_JSON", str(tmp_path / "missing_operator_context.json"))

    payload = MarketAPI().load_market_summary("mkt_777")

    assert payload["compact_gate_stack"]["source"] == "api"
    assert payload["compact_gate_stack"]["resolver_gate"] == "blocked"
    assert payload["compact_gate_stack"]["recommended_operator_action"] == "review_resolver_contract"
    assert payload["promotion_state"]["demotion_reason"] == "validation_freshness_unhealthy"
    assert payload["top_parameter_view"]["schema_version"] == "top_parameter_view.v1"
