from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from weather_comparison_engine.status.gate_stack_consumer import consume_gate_stack_payload
from weather_comparison_engine.status.gate_stack_automation_runner import build_exit_code_matrix

AUTOMATION_SUMMARY_SCHEMA_VERSION = "gate_stack_automation_summary.v1"


def build_automation_summary(
    gate_stack_api: dict | None,
    *,
    market_id: str | None = None,
    now: datetime | None = None,
) -> dict:
    payload = gate_stack_api if isinstance(gate_stack_api, dict) else {}
    timestamp = now or datetime.now(timezone.utc)
    consumer = consume_gate_stack_payload(payload, market_id=market_id)
    selected_market = str(market_id or payload.get("market_id") or "")
    source = consumer.market_view if isinstance(consumer.market_view, dict) else consumer.payload

    gate_stack = source.get("gate_stack") if isinstance(source.get("gate_stack"), dict) else source
    block_reasons = [str(item) for item in source.get("block_reasons") or payload.get("block_reasons") or []]
    primary_block_reason = str(
        source.get("primary_block_reason")
        or payload.get("primary_block_reason")
        or (block_reasons[0] if block_reasons else "")
    )
    can_execute = bool(source.get("can_execute", payload.get("can_execute", False)))
    severity = str(source.get("severity") or payload.get("severity") or _severity(primary_block_reason, can_execute))
    recommended_operator_action = str(
        source.get("recommended_operator_action")
        or payload.get("recommended_operator_action")
        or _recommended_action(primary_block_reason, can_execute)
    )
    gate_source = consumer.gate_source

    return {
        "schema_version": AUTOMATION_SUMMARY_SCHEMA_VERSION,
        "generated_at": timestamp.isoformat(),
        "source_schema_version": str(payload.get("schema_version") or "unknown"),
        "gate_source": gate_source,
        "market_id": selected_market or None,
        "can_execute": can_execute,
        "severity": severity,
        "recommended_operator_action": recommended_operator_action,
        "primary_block_reason": primary_block_reason or None,
        "block_reasons": block_reasons,
        "gate_stack": {
            "data_gate": str(gate_stack.get("data_gate") or "-"),
            "resolver_gate": str(gate_stack.get("resolver_gate") or "-"),
            "probability_gate": str(gate_stack.get("probability_gate") or "-"),
            "freshness_gate": str(gate_stack.get("freshness_gate") or "-"),
            "authorization_gate": str(gate_stack.get("authorization_gate") or "-"),
            "execution_gate": str(gate_stack.get("execution_gate") or "-"),
        },
        "automation_signal": _automation_signal(
            can_execute=can_execute,
            severity=severity,
            recommended_operator_action=recommended_operator_action,
        ),
        "exit_code_policy": {
            "schema_version": "gate_stack_exit_code_policy.v1",
            "fail_on_signal": "red",
            "supported_fail_on_signals": ["red", "amber", "never"],
            "matrix": build_exit_code_matrix(),
        },
    }


def write_automation_summary(path: str | Path, summary: dict) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
def _severity(primary_block_reason: str, can_execute: bool) -> str:
    if can_execute:
        return "low"
    if primary_block_reason in {
        "stale_worker",
        "monitoring_not_healthy",
        "validation_freshness_unhealthy",
        "label_coverage_unhealthy",
    }:
        return "high"
    return "medium"


def _recommended_action(primary_block_reason: str, can_execute: bool) -> str:
    if can_execute:
        return "allow_live_execution"
    if primary_block_reason in {
        "resolver_not_matched",
        "resolver_confidence_low",
        "resolver_source_not_exact",
        "comparison_not_actionable",
    }:
        return "review_resolver_contract"
    if primary_block_reason in {
        "stale_worker",
        "monitoring_not_healthy",
        "validation_freshness_unhealthy",
        "label_coverage_unhealthy",
    }:
        return "refresh_pipeline_inputs"
    if primary_block_reason in {
        "probability_not_live_approved",
        "execution_constraint_not_live_allowed",
        "calibration_not_calibrated",
    }:
        return "manual_advisory_only"
    if primary_block_reason in {"execution_not_ready", "execution_not_live_ready"}:
        return "check_gateway_readiness"
    return "hold_execution_and_review"


def _automation_signal(*, can_execute: bool, severity: str, recommended_operator_action: str) -> str:
    if can_execute:
        return "green"
    if severity == "high":
        return "red"
    if recommended_operator_action in {"manual_advisory_only", "check_gateway_readiness"}:
        return "amber"
    return "amber"
