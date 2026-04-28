from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

GATE_STACK_API_SCHEMA_VERSION = "gate_stack_api.v1"
_GATE_KEYS = (
    "data_gate",
    "resolver_gate",
    "probability_gate",
    "freshness_gate",
    "authorization_gate",
    "execution_gate",
)


class GateStackAPIBuilder:
    def __init__(self, *, now: datetime | None = None) -> None:
        self.now = now or datetime.now(timezone.utc)

    def build(self, unified_status: dict | None, latest_dashboard_rows: list[dict] | None = None) -> dict:
        payload = unified_status if isinstance(unified_status, dict) else {}
        gate_stack = payload.get("gate_stack") if isinstance(payload.get("gate_stack"), dict) else {}
        current_market = payload.get("current_market") if isinstance(payload.get("current_market"), dict) else {}

        normalized = self._normalize_gate_stack(gate_stack)
        block_reasons = [str(item) for item in normalized.get("block_reasons") or []]
        can_execute = (
            normalized.get("authorization_gate") == "pass"
            and normalized.get("execution_gate") == "pass"
        )
        primary_block_reason = block_reasons[0] if block_reasons else None
        severity = _severity_for_reason(primary_block_reason, can_execute=can_execute)
        recommended_operator_action = _recommended_action_for_reason(
            primary_block_reason,
            can_execute=can_execute,
        )
        market_gate_views = self._build_market_gate_views(
            latest_dashboard_rows,
            global_gate_stack=normalized,
        )
        top_parameter_view = payload.get("top_parameter_view")
        source_policy = payload.get("source_policy")

        return {
            "schema_version": GATE_STACK_API_SCHEMA_VERSION,
            "generated_at": str(payload.get("generated_at") or self.now.isoformat()),
            "source_schema_version": str(payload.get("schema_version") or "unknown"),
            "overall_status": str(payload.get("overall_status") or "unknown"),
            "market_id": current_market.get("market_id"),
            "gate_stack": normalized,
            "block_reasons": block_reasons,
            "can_execute": can_execute,
            "primary_block_reason": primary_block_reason,
            "severity": severity,
            "recommended_operator_action": recommended_operator_action,
            "market_count": len(market_gate_views),
            "market_gate_views": market_gate_views,
            "top_parameter_view": top_parameter_view if isinstance(top_parameter_view, dict) else None,
            "source_policy": source_policy if isinstance(source_policy, dict) else None,
        }

    def write(
        self,
        path: str | Path,
        unified_status: dict | None,
        latest_dashboard_rows: list[dict] | None = None,
    ) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = self.build(unified_status, latest_dashboard_rows=latest_dashboard_rows)
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return out

    def _normalize_gate_stack(self, gate_stack: dict) -> dict:
        normalized: dict[str, object] = {}
        for gate in _GATE_KEYS:
            status = str(gate_stack.get(gate) or "blocked").lower()
            normalized[gate] = "pass" if status == "pass" else "blocked"
            reasons_key = f"{gate}_reasons"
            normalized[reasons_key] = [str(item) for item in gate_stack.get(reasons_key) or []]

        all_reasons: list[str] = []
        for gate in _GATE_KEYS:
            for reason in normalized.get(f"{gate}_reasons") or []:
                token = str(reason)
                if token not in all_reasons:
                    all_reasons.append(token)
        for reason in gate_stack.get("block_reasons") or []:
            token = str(reason)
            if token not in all_reasons:
                all_reasons.append(token)

        normalized["block_reasons"] = all_reasons
        return normalized

    def _build_market_gate_views(self, latest_dashboard_rows: list[dict] | None, *, global_gate_stack: dict) -> list[dict]:
        if not isinstance(latest_dashboard_rows, list):
            return []

        views: list[dict] = []
        seen_market_ids: set[str] = set()
        for row in latest_dashboard_rows:
            if not isinstance(row, dict):
                continue
            market_id = str(row.get("market_id") or "").strip()
            if not market_id or market_id in seen_market_ids:
                continue
            seen_market_ids.add(market_id)
            views.append(_build_market_gate_view(row=row, global_gate_stack=global_gate_stack))
        return views


def _build_market_gate_view(*, row: dict, global_gate_stack: dict) -> dict:
    comparison_status = str(row.get("comparison_status") or "")
    rule_status = str(row.get("rule_status") or "").lower()
    source_match_grade = str(row.get("source_match_grade") or "").lower()
    resolver_confidence_raw = row.get("resolver_confidence")
    try:
        resolver_confidence = (
            float(resolver_confidence_raw) if resolver_confidence_raw is not None else None
        )
    except Exception:
        resolver_confidence = None

    data_reasons: list[str] = []
    if comparison_status not in {"aligned", "mild_divergence", "strong_divergence"}:
        data_reasons.append("comparison_not_actionable")

    resolver_reasons: list[str] = []
    if rule_status not in {"matched", "matched_index", "matched_snapshot"}:
        resolver_reasons.append("resolver_not_matched")
    if resolver_confidence is None or resolver_confidence < 0.7:
        resolver_reasons.append("resolver_confidence_low")
    if source_match_grade in {"", "unmatched", "family_only"}:
        resolver_reasons.append("resolver_source_not_exact")

    probability_gate = str(global_gate_stack.get("probability_gate") or "blocked")
    probability_reasons = [str(item) for item in global_gate_stack.get("probability_gate_reasons") or []]
    freshness_gate = str(global_gate_stack.get("freshness_gate") or "blocked")
    freshness_reasons = [str(item) for item in global_gate_stack.get("freshness_gate_reasons") or []]
    execution_gate = str(global_gate_stack.get("execution_gate") or "blocked")
    execution_reasons = [str(item) for item in global_gate_stack.get("execution_gate_reasons") or []]

    authorization_reasons: list[str] = []
    for reason in resolver_reasons + probability_reasons + freshness_reasons:
        if reason not in authorization_reasons:
            authorization_reasons.append(reason)

    block_reasons: list[str] = []
    for reasons in (
        data_reasons,
        resolver_reasons,
        probability_reasons,
        freshness_reasons,
        authorization_reasons,
        execution_reasons,
    ):
        for reason in reasons:
            if reason not in block_reasons:
                block_reasons.append(reason)

    can_execute = (
        not authorization_reasons
        and execution_gate == "pass"
    )
    primary_block_reason = block_reasons[0] if block_reasons else None

    return {
        "market_id": row.get("market_id"),
        "market_question": row.get("market_question"),
        "comparison_status": comparison_status,
        "action_hint": row.get("action_hint"),
        "data_gate": "pass" if not data_reasons else "blocked",
        "data_gate_reasons": data_reasons,
        "resolver_gate": "pass" if not resolver_reasons else "blocked",
        "resolver_gate_reasons": resolver_reasons,
        "probability_gate": probability_gate,
        "probability_gate_reasons": probability_reasons,
        "freshness_gate": freshness_gate,
        "freshness_gate_reasons": freshness_reasons,
        "authorization_gate": "pass" if not authorization_reasons else "blocked",
        "authorization_gate_reasons": authorization_reasons,
        "execution_gate": execution_gate,
        "execution_gate_reasons": execution_reasons,
        "block_reasons": block_reasons,
        "can_execute": can_execute,
        "primary_block_reason": primary_block_reason,
        "severity": _severity_for_reason(primary_block_reason, can_execute=can_execute),
        "recommended_operator_action": _recommended_action_for_reason(
            primary_block_reason,
            can_execute=can_execute,
        ),
    }


def _severity_for_reason(primary_block_reason: str | None, *, can_execute: bool) -> str:
    if can_execute:
        return "low"
    reason = str(primary_block_reason or "")
    if reason in {
        "stale_worker",
        "monitoring_not_healthy",
        "validation_freshness_unhealthy",
        "label_coverage_unhealthy",
    }:
        return "high"
    if reason.startswith("resolver_") or reason.startswith("probability_"):
        return "medium"
    if reason in {
        "execution_constraint_not_live_allowed",
        "calibration_not_calibrated",
        "execution_not_ready",
        "execution_not_live_ready",
    }:
        return "medium"
    return "medium"


def _recommended_action_for_reason(primary_block_reason: str | None, *, can_execute: bool) -> str:
    if can_execute:
        return "allow_live_execution"
    reason = str(primary_block_reason or "")
    if reason in {
        "resolver_not_matched",
        "resolver_confidence_low",
        "resolver_source_not_exact",
        "comparison_not_actionable",
    }:
        return "review_resolver_contract"
    if reason in {"stale_worker", "monitoring_not_healthy", "validation_freshness_unhealthy", "label_coverage_unhealthy"}:
        return "refresh_pipeline_inputs"
    if reason in {"probability_not_live_approved", "execution_constraint_not_live_allowed", "calibration_not_calibrated"}:
        return "manual_advisory_only"
    if reason in {"execution_not_ready", "execution_not_live_ready"}:
        return "check_gateway_readiness"
    return "hold_execution_and_review"
