from __future__ import annotations

import json
from datetime import datetime, timezone

from typer.testing import CliRunner

from weather_comparison_engine import main as comparison_main
from weather_comparison_engine.status import (
    append_ops_alert,
    build_automation_summary,
    build_exit_code_matrix,
    build_gate_stack_contract_consistency_report,
    build_initial_trend,
    build_ops_alert_event,
    resolve_exit_code,
    should_emit_ops_alert,
    update_consistency_trend,
)


def test_build_automation_summary_uses_market_view() -> None:
    summary = build_automation_summary(
        {
            "schema_version": "gate_stack_api.v1",
            "market_id": "m-default",
            "can_execute": False,
            "primary_block_reason": "hold",
            "market_gate_views": [
                {
                    "market_id": "m-target",
                    "can_execute": False,
                    "severity": "high",
                    "recommended_operator_action": "refresh_pipeline_inputs",
                    "primary_block_reason": "stale_worker",
                    "block_reasons": ["stale_worker"],
                    "data_gate": "pass",
                    "resolver_gate": "pass",
                    "probability_gate": "pass",
                    "freshness_gate": "blocked",
                    "authorization_gate": "blocked",
                    "execution_gate": "blocked",
                }
            ],
        },
        market_id="m-target",
    )

    assert summary["schema_version"] == "gate_stack_automation_summary.v1"
    assert summary["market_id"] == "m-target"
    assert summary["severity"] == "high"
    assert summary["recommended_operator_action"] == "refresh_pipeline_inputs"
    assert summary["automation_signal"] == "red"
    assert summary["gate_stack"]["freshness_gate"] == "blocked"
    assert summary["gate_source"] == "api"
    assert summary["exit_code_policy"]["schema_version"] == "gate_stack_exit_code_policy.v1"
    assert summary["exit_code_policy"]["matrix"]["red"]["red"] == 2
    assert summary["exit_code_policy"]["matrix"]["amber"]["amber"] == 2


def test_build_gate_stack_automation_summary_cli_writes_report(monkeypatch, tmp_path) -> None:
    gate_stack_api_path = tmp_path / "gate_stack_api.json"
    automation_out = tmp_path / "gate_stack_automation_summary.json"

    gate_stack_api_path.write_text(
        json.dumps(
            {
                "schema_version": "gate_stack_api.v1",
                "market_id": "m-1",
                "can_execute": False,
                "primary_block_reason": "probability_not_live_approved",
                "block_reasons": ["probability_not_live_approved"],
                "gate_stack": {
                    "data_gate": "pass",
                    "resolver_gate": "pass",
                    "probability_gate": "blocked",
                    "freshness_gate": "pass",
                    "authorization_gate": "blocked",
                    "execution_gate": "blocked",
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(comparison_main, "GATE_STACK_API_JSON", gate_stack_api_path)
    monkeypatch.setattr(comparison_main, "GATE_STACK_AUTOMATION_SUMMARY_JSON", automation_out)

    result = CliRunner().invoke(comparison_main.app, ["build-gate-stack-automation-summary"])

    assert result.exit_code == 0
    assert automation_out.exists()
    payload = json.loads(automation_out.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "gate_stack_automation_summary.v1"
    assert payload["recommended_operator_action"] == "manual_advisory_only"
    assert payload["automation_signal"] == "amber"
    assert payload["gate_source"] == "api"


def test_build_automation_summary_uses_contract_gate_source_when_provided() -> None:
    summary = build_automation_summary(
        {
            "schema_version": "gate_stack_api.v1",
            "contracts": {"gate_source": "unified_fallback"},
            "gate_stack": {
                "data_gate": "pass",
                "resolver_gate": "pass",
                "probability_gate": "pass",
                "freshness_gate": "pass",
                "authorization_gate": "pass",
                "execution_gate": "pass",
                "block_reasons": [],
            },
            "can_execute": True,
        }
    )
    assert summary["gate_source"] == "unified_fallback"


def test_resolve_exit_code_by_signal_level() -> None:
    assert resolve_exit_code({"automation_signal": "green"}, fail_on_signal="red") == 0
    assert resolve_exit_code({"automation_signal": "amber"}, fail_on_signal="red") == 0
    assert resolve_exit_code({"automation_signal": "red"}, fail_on_signal="red") == 2
    assert resolve_exit_code({"automation_signal": "amber"}, fail_on_signal="amber") == 2
    assert resolve_exit_code({"automation_signal": "red"}, fail_on_signal="amber") == 2
    assert resolve_exit_code({"automation_signal": "red"}, fail_on_signal="never") == 0
    assert build_exit_code_matrix()["never"]["red"] == 0
    assert build_exit_code_matrix()["amber"]["amber"] == 2


def test_run_gate_stack_automation_check_cli_returns_non_zero_on_red(monkeypatch, tmp_path) -> None:
    unified_path = tmp_path / "unified_status.json"
    latest_rows_path = tmp_path / "latest_dashboard_rows.json"
    gate_stack_api_out = tmp_path / "gate_stack_api.json"
    automation_out = tmp_path / "gate_stack_automation_summary.json"
    ops_alerts_path = tmp_path / "gate_stack_ops_alerts.jsonl"

    unified_path.write_text(
        json.dumps(
            {
                "schema_version": "unified_status.v1",
                "generated_at": "2026-04-19T10:00:00+00:00",
                "overall_status": "guarded",
                "current_market": {"market_id": "m-9"},
                "gate_stack": {
                    "data_gate": "pass",
                    "data_gate_reasons": [],
                    "resolver_gate": "pass",
                    "resolver_gate_reasons": [],
                    "probability_gate": "pass",
                    "probability_gate_reasons": [],
                    "freshness_gate": "blocked",
                    "freshness_gate_reasons": ["stale_worker"],
                    "authorization_gate": "blocked",
                    "authorization_gate_reasons": ["stale_worker"],
                    "execution_gate": "blocked",
                    "execution_gate_reasons": ["execution_not_ready"],
                    "block_reasons": ["stale_worker", "execution_not_ready"],
                },
            }
        ),
        encoding="utf-8",
    )
    latest_rows_path.write_text(
        json.dumps(
            [
                {
                    "market_id": "m-9",
                    "market_question": "Q9",
                    "comparison_status": "aligned",
                    "rule_status": "matched",
                    "resolver_confidence": 0.92,
                    "source_match_grade": "exact_station",
                }
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(comparison_main, "UNIFIED_STATUS_JSON", unified_path)
    monkeypatch.setattr(comparison_main, "LATEST_DASHBOARD_ROWS_JSON", latest_rows_path)
    monkeypatch.setattr(comparison_main, "GATE_STACK_API_JSON", gate_stack_api_out)
    monkeypatch.setattr(comparison_main, "GATE_STACK_AUTOMATION_SUMMARY_JSON", automation_out)
    monkeypatch.setattr(comparison_main, "GATE_STACK_OPS_ALERTS_JSONL", ops_alerts_path)

    result = CliRunner().invoke(
        comparison_main.app,
        ["run-gate-stack-automation-check", "--fail-on-signal", "red"],
    )

    assert result.exit_code == 2
    assert gate_stack_api_out.exists()
    assert automation_out.exists()
    assert ops_alerts_path.exists()
    lines = [line for line in ops_alerts_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1


def test_ops_alert_bridge_emits_for_red_only(tmp_path) -> None:
    summary_red = {
        "schema_version": "gate_stack_automation_summary.v1",
        "market_id": "m-1",
        "automation_signal": "red",
        "severity": "high",
        "primary_block_reason": "stale_worker",
        "recommended_operator_action": "refresh_pipeline_inputs",
        "block_reasons": ["stale_worker"],
    }
    summary_amber = {
        "schema_version": "gate_stack_automation_summary.v1",
        "automation_signal": "amber",
    }
    assert should_emit_ops_alert(summary_red, exit_code=2) is True
    assert should_emit_ops_alert(summary_amber, exit_code=2) is False
    assert should_emit_ops_alert(summary_red, exit_code=0) is False

    event = build_ops_alert_event(
        summary=summary_red,
        fail_on_signal="red",
        exit_code=2,
        cycle=7,
        now=datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc),
    )
    alerts_path = tmp_path / "alerts.jsonl"
    append_ops_alert(alerts_path, event)
    payload = alerts_path.read_text(encoding="utf-8").strip()
    assert "gate_stack_ops_alert.v1" in payload
    assert "\"cycle\": 7" in payload
    assert "\"gate_source\": \"api\"" in payload
    assert "\"delivery_state\": \"pending\"" in payload
    assert "\"suppressed_count\": 0" in payload
    assert "\"dedupe_key\":" in payload


def test_contract_consistency_report_detects_alignment() -> None:
    gate_stack_api = {
        "schema_version": "gate_stack_api.v1",
        "market_id": "m-1",
        "can_execute": False,
        "severity": "high",
        "primary_block_reason": "stale_worker",
        "recommended_operator_action": "refresh_pipeline_inputs",
        "block_reasons": ["stale_worker"],
    }
    summary = {
        "schema_version": "gate_stack_automation_summary.v1",
        "source_schema_version": "gate_stack_api.v1",
        "market_id": "m-1",
        "can_execute": False,
        "severity": "high",
        "primary_block_reason": "stale_worker",
        "recommended_operator_action": "refresh_pipeline_inputs",
        "block_reasons": ["stale_worker"],
        "gate_source": "api",
    }
    report = build_gate_stack_contract_consistency_report(gate_stack_api, summary)
    assert report["passed"] is True
    assert report["mismatch_count"] == 0
    assert report["fallback_stats"]["api"] == 1


def test_contract_consistency_report_detects_mismatch() -> None:
    report = build_gate_stack_contract_consistency_report(
        {"schema_version": "gate_stack_api.v1", "can_execute": True},
        {
            "source_schema_version": "gate_stack_api.v1",
            "market_id": "m-2",
            "can_execute": False,
            "gate_source": "api",
        },
        market_id="m-1",
    )
    assert report["passed"] is False
    assert report["mismatch_count"] >= 1
    bucket_counts = report["mismatch_buckets"]["counts"]
    assert sum(bucket_counts.values()) == report["mismatch_count"]


def test_contract_consistency_report_with_runtime_snapshots() -> None:
    report = build_gate_stack_contract_consistency_report(
        {
            "schema_version": "gate_stack_api.v1",
            "generated_at": "2026-04-19T10:00:00+00:00",
            "market_id": "m-1",
            "can_execute": False,
            "severity": "high",
            "primary_block_reason": "resolver_not_matched",
            "recommended_operator_action": "review_resolver_contract",
            "block_reasons": ["resolver_not_matched"],
        },
        {
            "schema_version": "gate_stack_automation_summary.v1",
            "source_schema_version": "gate_stack_api.v1",
            "generated_at": "2026-04-19T10:00:05+00:00",
            "market_id": "m-1",
            "can_execute": False,
            "severity": "high",
            "primary_block_reason": "resolver_not_matched",
            "recommended_operator_action": "review_resolver_contract",
            "block_reasons": ["resolver_not_matched"],
            "gate_source": "api",
        },
        telegram_runtime_snapshot={
            "schema_version": "telegram_gate_runtime_snapshot.v1",
            "generated_at": "2026-04-19T10:00:06+00:00",
            "market_id": "m-1",
            "block_reasons": ["resolver_not_matched"],
            "gate_source": "api",
        },
        gateway_runtime_snapshot={
            "schema_version": "gateway_gate_runtime_snapshot.v1",
            "generated_at": "2026-04-19T10:00:06+00:00",
            "market_id": "m-1",
            "block_reasons": ["resolver_not_matched"],
            "gate_source": "api",
        },
    )
    assert report["passed"] is True
    assert report["fallback_stats"]["api"] == 3
    assert report["schema_health"]["level"] == "ok"
    assert report["mismatch_buckets"]["counts"]["schema_drift"] == 0


def test_consistency_trend_accumulates_bucket_totals() -> None:
    trend = build_initial_trend()
    trend = update_consistency_trend(
        trend,
        report={
            "passed": False,
            "mismatch_count": 2,
            "mismatch_buckets": {
                "counts": {
                    "schema_drift": 1,
                    "source_drift": 1,
                    "reason_drift": 0,
                    "other_drift": 0,
                }
            },
        },
        cycle=1,
        timestamp="2026-04-19T11:00:00+00:00",
    )
    trend = update_consistency_trend(
        trend,
        report={
            "passed": True,
            "mismatch_count": 0,
            "mismatch_buckets": {
                "counts": {
                    "schema_drift": 0,
                    "source_drift": 0,
                    "reason_drift": 0,
                    "other_drift": 0,
                }
            },
        },
        cycle=2,
        timestamp="2026-04-19T11:01:00+00:00",
    )
    assert trend["schema_version"] == "gate_stack_contract_consistency_trend.v1"
    assert trend["total_cycles"] == 2
    assert trend["mismatch_cycles"] == 1
    assert trend["bucket_totals"]["schema_drift"] == 1
    assert trend["bucket_totals"]["source_drift"] == 1
    assert len(trend["recent_cycles"]) == 2


def test_check_gate_stack_contract_consistency_cli(monkeypatch, tmp_path) -> None:
    gate_stack_api_path = tmp_path / "gate_stack_api.json"
    summary_path = tmp_path / "gate_stack_automation_summary.json"
    out_path = tmp_path / "gate_stack_contract_consistency.json"

    gate_stack_api_path.write_text(
        json.dumps(
            {
                "schema_version": "gate_stack_api.v1",
                "market_id": "m-1",
                "can_execute": False,
                "severity": "high",
                "primary_block_reason": "stale_worker",
                "recommended_operator_action": "refresh_pipeline_inputs",
                "block_reasons": ["stale_worker"],
            }
        ),
        encoding="utf-8",
    )
    summary_path.write_text(
        json.dumps(
            {
                "schema_version": "gate_stack_automation_summary.v1",
                "source_schema_version": "gate_stack_api.v1",
                "market_id": "m-1",
                "can_execute": False,
                "severity": "high",
                "primary_block_reason": "stale_worker",
                "recommended_operator_action": "refresh_pipeline_inputs",
                "block_reasons": ["stale_worker"],
                "gate_source": "api",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(comparison_main, "GATE_STACK_API_JSON", gate_stack_api_path)
    monkeypatch.setattr(comparison_main, "GATE_STACK_AUTOMATION_SUMMARY_JSON", summary_path)
    monkeypatch.setattr(comparison_main, "GATE_STACK_CONTRACT_CONSISTENCY_JSON", out_path)
    monkeypatch.setattr(
        comparison_main,
        "TELEGRAM_GATE_RUNTIME_SNAPSHOT_JSON",
        tmp_path / "missing_telegram_gate_runtime_snapshot.json",
    )
    monkeypatch.setattr(
        comparison_main,
        "GATEWAY_GATE_RUNTIME_SNAPSHOT_JSON",
        tmp_path / "missing_gateway_gate_runtime_snapshot.json",
    )

    result = CliRunner().invoke(comparison_main.app, ["check-gate-stack-contract-consistency"])
    assert result.exit_code == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "gate_stack_contract_consistency.v1"
    assert payload["passed"] is True
