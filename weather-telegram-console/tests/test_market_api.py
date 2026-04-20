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
    assert payload["promotion_state"] == {}


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
