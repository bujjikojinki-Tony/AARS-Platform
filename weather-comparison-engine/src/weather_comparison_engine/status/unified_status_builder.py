from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from weather_comparison_engine.probability.promotion_policy import PromotionPolicy
from weather_comparison_engine.status.top_parameter_view import build_top_parameter_view


class UnifiedStatusBuilder:
    def __init__(self, *, now: datetime | None = None) -> None:
        self.now = now or datetime.now(timezone.utc)

    def build(
        self,
        *,
        monitoring_report: dict | None,
        latest_dashboard_rows: list[dict] | None,
        probability_shadow_report: dict | None,
        production_readiness_report: dict | None,
        validation_freshness_status: dict | None = None,
        label_coverage_report: dict | None = None,
        source_policy_status: dict | None = None,
    ) -> dict:
        current_market = _first_row(latest_dashboard_rows)
        market_id = str((current_market or {}).get("market_id") or "")
        probability_state = _find_probability_state(probability_shadow_report, market_id)
        promotion_state = _build_promotion_state(
            probability_state=probability_state,
            current_market=current_market,
            validation_freshness_status=validation_freshness_status,
            label_coverage_report=label_coverage_report,
        )
        monitoring = _build_monitoring_section(monitoring_report)
        probability = _build_probability_section(probability_state, promotion_state=promotion_state)
        execution = _build_execution_section(production_readiness_report)
        market = _build_market_section(current_market)
        validation = _build_validation_section(
            validation_freshness_status,
            label_coverage_report,
            promotion_state=promotion_state,
        )
        source_policy = _build_source_policy_section(source_policy_status)
        top_parameter_view = _build_top_parameter_view(
            current_market=current_market,
            probability=probability,
            gate_stack=None,
        )
        block_reasons = _build_block_reasons(
            monitoring=monitoring,
            probability=probability,
            execution=execution,
            market=market,
            validation=validation,
            source_policy=source_policy,
        )
        gate_stack = _build_gate_stack(
            monitoring=monitoring,
            probability=probability,
            execution=execution,
            market=market,
            validation=validation,
            source_policy=source_policy,
        )
        can_bot_trade = _can_bot_trade(
            monitoring=monitoring,
            probability=probability,
            execution=execution,
            market=market,
            validation=validation,
            source_policy=source_policy,
        )
        operator_mode = _resolve_operator_mode(execution=execution)
        operator = {
            "can_bot_trade": can_bot_trade,
            "human_action_required": not can_bot_trade,
            "execution_mode": (
                "autonomous_allowed"
                if can_bot_trade
                else str(probability.get("execution_constraint") or "manual_advisory_only")
            ),
            "operator_mode": operator_mode,
            "mode_badge": _mode_badge(operator_mode),
            "dev_controls_enabled": operator_mode == "dev_local_harness",
        }

        return {
            "schema_version": "unified_status.v1",
            "generated_at": self.now.isoformat(),
            "overall_status": _overall_status(
                monitoring=monitoring,
                execution=execution,
                can_bot_trade=can_bot_trade,
            ),
            "current_market": market,
            "monitoring": monitoring,
            "probability": probability,
            "validation": validation,
            "execution": execution,
            "operator": operator,
            "gate_stack": gate_stack,
            "block_reasons": block_reasons,
            "top_parameter_view": top_parameter_view,
            "source_policy": source_policy,
        }

    def write(
        self,
        path: str | Path,
        *,
        monitoring_report: dict | None,
        latest_dashboard_rows: list[dict] | None,
        probability_shadow_report: dict | None,
        production_readiness_report: dict | None,
        validation_freshness_status: dict | None = None,
        label_coverage_report: dict | None = None,
        source_policy_status: dict | None = None,
    ) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = self.build(
            monitoring_report=monitoring_report,
            latest_dashboard_rows=latest_dashboard_rows,
            probability_shadow_report=probability_shadow_report,
            production_readiness_report=production_readiness_report,
            validation_freshness_status=validation_freshness_status,
            label_coverage_report=label_coverage_report,
            source_policy_status=source_policy_status,
        )
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return out


def _first_row(rows: list[dict] | None) -> dict:
    if not rows:
        return {}
    first = rows[0]
    return first if isinstance(first, dict) else {}


def _find_probability_state(report: dict | None, market_id: str) -> dict:
    if not report:
        return {}
    states = report.get("states") or []
    if not isinstance(states, list):
        return {}
    for state in states:
        if isinstance(state, dict) and str(state.get("market_id") or "") == market_id:
            return state
    for state in states:
        if isinstance(state, dict):
            return state
    return {}


def _build_monitoring_section(report: dict | None) -> dict:
    report = report or {}
    workers = []
    for worker in report.get("workers", []):
        if not isinstance(worker, dict):
            continue
        workers.append(
            {
                "label": str(worker.get("label") or worker.get("worker") or "worker"),
                "layer": str(worker.get("layer") or "-"),
                "status": str(worker.get("status") or "warning"),
                "freshness_seconds": worker.get("freshness_seconds"),
                "last_success_at": worker.get("last_success_at"),
            }
        )
    return {
        "overall_status": str(report.get("overall_status") or "unknown"),
        "counts": report.get("counts") or {},
        "worker_count": len(workers),
        "workers": workers,
    }


def _build_probability_section(state: dict | None, *, promotion_state: dict | None = None) -> dict:
    state = state or {}
    probability_contract = state.get("probability_contract")
    if not isinstance(probability_contract, dict):
        probability_contract = {
            "contract_version": "probability_contract.v1",
            "probability_mode": str(state.get("probability_mode") or "unknown"),
            "execution_constraint": str(state.get("execution_constraint") or "manual_advisory_only"),
            "calibration_status": str(state.get("calibration_status") or "unknown"),
        }
    return {
        "market_id": state.get("market_id"),
        "base_probability_mode": str(state.get("probability_mode") or "unknown"),
        "base_execution_constraint": str(state.get("execution_constraint") or "manual_advisory_only"),
        "probability_mode": str(
            (promotion_state or {}).get("probability_mode")
            or state.get("probability_mode")
            or "unknown"
        ),
        "execution_constraint": str(
            (promotion_state or {}).get("execution_constraint")
            or state.get("execution_constraint")
            or "manual_advisory_only"
        ),
        "calibration_status": str(
            (promotion_state or {}).get("calibration_status")
            or state.get("calibration_status")
            or "unknown"
        ),
        "contract_version": str(probability_contract.get("contract_version") or "probability_contract.v1"),
        "probability_contract": probability_contract,
        "confidence_adjusted_edge": state.get("confidence_adjusted_edge"),
        "confidence_score": state.get("confidence_score"),
        "resolver_status": state.get("resolver_status"),
        "promotion_state": promotion_state or {},
    }


def _build_execution_section(report: dict | None) -> dict:
    report = report or {}
    return {
        "status": str(report.get("status") or "unknown"),
        "ready_for_live": bool(report.get("ready_for_live", False)),
        "decision": str(report.get("decision") or "-"),
        "blocking_count": int(report.get("blocking_count") or 0),
        "warning_count": int(report.get("warning_count") or 0),
    }


def _build_validation_section(
    freshness_status: dict | None,
    coverage_report: dict | None,
    *,
    promotion_state: dict | None = None,
) -> dict:
    freshness_status = freshness_status or {}
    coverage_report = coverage_report or {}
    return {
        "freshness_status": str(freshness_status.get("status") or "unknown"),
        "freshness_seconds": freshness_status.get("freshness_seconds"),
        "freshness_reason": str(freshness_status.get("reason") or "-"),
        "label_coverage_status": str(coverage_report.get("status") or "unknown"),
        "labeled_rows": coverage_report.get("labeled_rows"),
        "labeled_ratio": coverage_report.get("labeled_ratio"),
        "coverage_blockers": [str(item) for item in coverage_report.get("blockers") or []],
        "promotion_state": promotion_state or {},
    }


def _build_source_policy_section(source_policy_status: dict | None) -> dict:
    source_policy_status = source_policy_status or {}
    sources = source_policy_status.get("sources") or []
    problem_sources = source_policy_status.get("problem_sources") or []
    freshness_counts = source_policy_status.get("counts") or {}
    return {
        "schema_version": str(source_policy_status.get("schema_version") or "source_policy_status.v1"),
        "overall_status": str(source_policy_status.get("overall_status") or "unknown"),
        "registry_schema_version": str(source_policy_status.get("registry_schema_version") or "-"),
        "fresh_count": int(freshness_counts.get("fresh") or 0),
        "stale_count": int(freshness_counts.get("stale") or 0),
        "unavailable_count": int(freshness_counts.get("unavailable") or 0),
        "priority_counts": source_policy_status.get("priority_counts") or {},
        "source_count": len(sources),
        "problem_sources": problem_sources[:5],
        "sources": sources,
    }


def _build_market_section(row: dict | None) -> dict:
    row = row or {}
    return {
        "market_id": row.get("market_id"),
        "market_question": row.get("market_question"),
        "comparison_status": row.get("comparison_status"),
        "confidence_adjusted_gap": row.get("confidence_adjusted_gap"),
        "action_hint": row.get("action_hint"),
        "market_probability": row.get("market_probability"),
        "rule_status": row.get("rule_status"),
        "resolver_confidence": row.get("resolver_confidence"),
        "source_match_grade": row.get("source_match_grade"),
        "market_snapshot_ref": row.get("market_snapshot_ref"),
        "forecast_snapshot_ref": row.get("forecast_snapshot_ref"),
    }


def _build_top_parameter_view(
    *,
    current_market: dict | None,
    probability: dict | None,
    gate_stack: dict | None,
) -> dict:
    current_market = current_market or {}
    probability = probability or {}
    gate_stack = gate_stack or {}
    return build_top_parameter_view(
        current_market=current_market,
        forecast_snapshot=current_market,
        comparison_point={
            **probability,
            **gate_stack,
            "comparison_status": current_market.get("comparison_status"),
            "required_data_source": current_market.get("required_data_source"),
        },
    )


def _infer_unit(market_family: str) -> str:
    family = str(market_family or "").lower()
    if "temperature" in family:
        return "celsius"
    if "precipitation" in family:
        return "mm"
    if "wind" in family:
        return "m/s"
    if "snow" in family:
        return "cm"
    if "sea_ice" in family:
        return "km²"
    return "-"


def _build_block_reasons(
    *,
    monitoring: dict,
    probability: dict,
    execution: dict,
    market: dict,
    validation: dict,
    source_policy: dict | None = None,
) -> list[str]:
    reasons: list[str] = []
    monitoring_status = str(monitoring.get("overall_status") or "unknown")
    if monitoring_status != "healthy":
        reasons.append(f"monitoring:{monitoring_status}")

    for worker in monitoring.get("workers", []):
        if worker.get("status") != "healthy":
            reasons.append(f"worker:{worker.get('label')}:{worker.get('status')}")

    comparison_status = str(market.get("comparison_status") or "unknown")
    if comparison_status in {"unknown", "-", "", "market_mismatch", "unmatched_rule"}:
        reasons.append(f"comparison:{comparison_status}")

    rule_status = str(market.get("rule_status") or "unknown")
    if rule_status not in {"matched", "matched_index", "matched_snapshot"}:
        reasons.append(f"resolver:{rule_status}")

    probability_mode = str(probability.get("probability_mode") or "unknown")
    if probability_mode != "live_approved":
        reasons.append(f"probability_mode:{probability_mode}")

    execution_constraint = str(probability.get("execution_constraint") or "manual_advisory_only")
    if execution_constraint != "live_execution_allowed":
        reasons.append(f"execution_constraint:{execution_constraint}")

    freshness_status = str(validation.get("freshness_status") or "unknown")
    if freshness_status != "healthy":
        reasons.append(f"validation_freshness:{freshness_status}")

    coverage_status = str(validation.get("label_coverage_status") or "unknown")
    if coverage_status != "healthy":
        reasons.append(f"label_coverage:{coverage_status}")
    for blocker in validation.get("coverage_blockers") or []:
        reasons.append(f"coverage_blocker:{blocker}")

    source_policy = source_policy or {}
    source_policy_status = str(source_policy.get("overall_status") or "unknown")
    if source_policy_status != "healthy":
        reasons.append(f"source_policy:{source_policy_status}")

    execution_status = str(execution.get("status") or "unknown")
    if execution_status != "ready":
        reasons.append(f"execution:{execution_status}")

    return reasons


def _can_bot_trade(
    *,
    monitoring: dict,
    probability: dict,
    execution: dict,
    market: dict,
    validation: dict,
    source_policy: dict | None = None,
) -> bool:
    monitoring_healthy = str(monitoring.get("overall_status") or "") == "healthy"
    comparison_status = str(market.get("comparison_status") or "")
    probability_live = str(probability.get("probability_mode") or "") == "live_approved"
    constraint_live = str(probability.get("execution_constraint") or "") == "live_execution_allowed"
    execution_ready = bool(execution.get("ready_for_live")) and str(execution.get("status") or "") == "ready"
    comparison_actionable = comparison_status in {"aligned", "mild_divergence", "strong_divergence"}
    validation_fresh = str(validation.get("freshness_status") or "") == "healthy"
    coverage_healthy = str(validation.get("label_coverage_status") or "") == "healthy"
    source_policy_healthy = str((source_policy or {}).get("overall_status") or "") == "healthy"
    return all(
        [
            monitoring_healthy,
            comparison_actionable,
            probability_live,
            constraint_live,
            validation_fresh,
            coverage_healthy,
            source_policy_healthy,
            execution_ready,
        ]
    )


def _build_gate_stack(
    *,
    monitoring: dict,
    probability: dict,
    execution: dict,
    market: dict,
    validation: dict,
    source_policy: dict | None = None,
) -> dict:
    data_reasons: list[str] = []
    if str(monitoring.get("overall_status") or "").lower() != "healthy":
        data_reasons.append("monitoring_not_healthy")
    comparison_status = str(market.get("comparison_status") or "")
    if comparison_status not in {"aligned", "mild_divergence", "strong_divergence"}:
        data_reasons.append("comparison_not_actionable")

    resolver_reasons: list[str] = []
    rule_status = str(market.get("rule_status") or "")
    if rule_status not in {"matched", "matched_index", "matched_snapshot"}:
        resolver_reasons.append("resolver_not_matched")
    resolver_confidence = market.get("resolver_confidence")
    try:
        confidence = float(resolver_confidence) if resolver_confidence is not None else None
    except Exception:
        confidence = None
    if confidence is None or confidence < 0.7:
        resolver_reasons.append("resolver_confidence_low")
    source_match_grade = str(market.get("source_match_grade") or "").lower()
    if source_match_grade in {"", "unmatched", "family_only"}:
        resolver_reasons.append("resolver_source_not_exact")

    probability_reasons: list[str] = []
    if str(probability.get("probability_mode") or "") != "live_approved":
        probability_reasons.append("probability_not_live_approved")
    if str(probability.get("execution_constraint") or "") != "live_execution_allowed":
        probability_reasons.append("execution_constraint_not_live_allowed")
    if str(probability.get("calibration_status") or "") != "calibrated":
        probability_reasons.append("calibration_not_calibrated")

    freshness_reasons: list[str] = []
    if str(monitoring.get("overall_status") or "").lower() != "healthy":
        freshness_reasons.append("monitoring_not_healthy")
    for worker in monitoring.get("workers", []):
        if str(worker.get("status") or "").lower() != "healthy":
            freshness_reasons.append("stale_worker")
            break
    if str(validation.get("freshness_status") or "").lower() != "healthy":
        freshness_reasons.append("validation_freshness_unhealthy")
    if str(validation.get("label_coverage_status") or "").lower() != "healthy":
        freshness_reasons.append("label_coverage_unhealthy")
    if str((source_policy or {}).get("overall_status") or "").lower() != "healthy":
        freshness_reasons.append("source_policy_unhealthy")

    execution_reasons: list[str] = []
    if str(execution.get("status") or "").lower() != "ready":
        execution_reasons.append("execution_not_ready")
    if not bool(execution.get("ready_for_live")):
        execution_reasons.append("execution_not_live_ready")

    authorization_reasons: list[str] = []
    for reason in resolver_reasons + probability_reasons + freshness_reasons:
        if reason not in authorization_reasons:
            authorization_reasons.append(reason)

    all_reasons: list[str] = []
    for bucket in (
        data_reasons,
        resolver_reasons,
        probability_reasons,
        freshness_reasons,
        execution_reasons,
    ):
        for reason in bucket:
            if reason not in all_reasons:
                all_reasons.append(reason)

    return {
        "data_gate": "pass" if not data_reasons else "blocked",
        "data_gate_reasons": data_reasons,
        "resolver_gate": "pass" if not resolver_reasons else "blocked",
        "resolver_gate_reasons": resolver_reasons,
        "probability_gate": "pass" if not probability_reasons else "blocked",
        "probability_gate_reasons": probability_reasons,
        "freshness_gate": "pass" if not freshness_reasons else "blocked",
        "freshness_gate_reasons": freshness_reasons,
        "authorization_gate": "pass" if not authorization_reasons else "blocked",
        "authorization_gate_reasons": authorization_reasons,
        "execution_gate": "pass" if not execution_reasons else "blocked",
        "execution_gate_reasons": execution_reasons,
        "block_reasons": all_reasons,
    }


def _build_promotion_state(
    *,
    probability_state: dict,
    current_market: dict,
    validation_freshness_status: dict | None,
    label_coverage_report: dict | None,
) -> dict:
    return PromotionPolicy().evaluate(
        probability_state=probability_state,
        validation_report={
            "probability_mode": probability_state.get("probability_mode"),
            "execution_constraint": probability_state.get("execution_constraint"),
            "calibration_status": probability_state.get("calibration_status"),
            "approved_for_live": probability_state.get("approved_for_live", False),
            "promotion_reason": probability_state.get("promotion_reason"),
            "probability_contract": probability_state.get("probability_contract"),
            "resolver_quality": {
                "resolver_match_rate": current_market.get("resolver_confidence"),
                "source_match_grade": current_market.get("source_match_grade"),
            },
        },
        validation_freshness_status=validation_freshness_status,
        label_coverage_report=label_coverage_report,
        resolver_quality={
            "resolver_match_rate": current_market.get("resolver_confidence"),
            "source_match_grade": current_market.get("source_match_grade"),
        },
    )


def _overall_status(*, monitoring: dict, execution: dict, can_bot_trade: bool) -> str:
    monitoring_status = str(monitoring.get("overall_status") or "unknown")
    if monitoring_status in {"degraded", "missing"}:
        return "degraded"
    if can_bot_trade:
        return "live_ready"
    if str(execution.get("status") or "unknown") == "blocked":
        return "guarded"
    return "warning"


def _resolve_operator_mode(*, execution: dict) -> str:
    configured = str(os.getenv("AARS_OPERATOR_MODE") or "").strip().lower()
    if configured in {"dev_local_harness", "dry_run_guarded", "production_read_only"}:
        return configured

    enable_dev = str(os.getenv("AARS_ENABLE_DEV_HARNESS") or "").strip().lower()
    if enable_dev in {"1", "true", "yes", "on"}:
        return "dev_local_harness"

    if bool(execution.get("ready_for_live")) and str(execution.get("status") or "") == "ready":
        return "production_read_only"

    return "dry_run_guarded"


def _mode_badge(operator_mode: str) -> dict[str, str]:
    mapping = {
        "dev_local_harness": {
            "label": "DEV LOCAL HARNESS",
            "tone": "warning",
            "description": "Local verification mode with development-only harness controls visible.",
        },
        "dry_run_guarded": {
            "label": "DRY-RUN GUARDED",
            "tone": "info",
            "description": "Guarded operator mode. Manual advisory and dry-run checks are allowed; no live execution.",
        },
        "production_read_only": {
            "label": "PRODUCTION READ-ONLY",
            "tone": "neutral",
            "description": "Production observation mode. Dev-only controls stay hidden and the console is read-only oriented.",
        },
    }
    return mapping.get(
        operator_mode,
        {
            "label": "UNKNOWN MODE",
            "tone": "warning",
            "description": "Operator mode is not recognized.",
        },
    )


def load_optional_json(path: str | Path) -> dict | list | None:
    src = Path(path)
    if not src.exists():
        return None
    try:
        payload = json.loads(src.read_text(encoding="utf-8"))
    except Exception:
        return None
    if isinstance(payload, (dict, list)):
        return payload
    return None
