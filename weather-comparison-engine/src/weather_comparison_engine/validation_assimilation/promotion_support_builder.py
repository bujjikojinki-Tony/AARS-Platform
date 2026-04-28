from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_promotion_decision_support(
    *,
    scope_type: str,
    scope_id: str,
    validation_summary: dict[str, Any] | None = None,
    validation_freshness: dict[str, Any] | None = None,
    coverage_summary: dict[str, Any] | None = None,
    policy_refs: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict:
    timestamp = now or datetime.now(timezone.utc)
    validation_summary = validation_summary or {}
    validation_freshness = validation_freshness or {}
    coverage_summary = coverage_summary or {}
    policy_refs = policy_refs or {}

    validation_status = str(validation_summary.get("validation_status") or "insufficient")
    freshness_status = str(validation_freshness.get("status") or "").lower()
    blockers = list(validation_summary.get("reasons") or [])
    if freshness_status in {"warning", "blocked", "missing"}:
        blockers.append(f"freshness:{freshness_status}")
    if _to_float(coverage_summary.get("label_coverage")) < 0.5:
        blockers.append("insufficient_label_coverage")
    if _to_float(coverage_summary.get("source_coverage")) < 0.5:
        blockers.append("weak_source_coverage")
    if _to_float(validation_summary.get("normalization_consistency")) < 0.5:
        blockers.append("normalization_inconsistency")

    promotion_readiness = "ready" if validation_status == "strong" and not blockers else "conditional" if blockers else "not_ready"
    current_probability_mode = str(
        validation_summary.get("current_probability_mode")
        or validation_summary.get("probability_mode")
        or "unknown"
    )

    promotion_reason = (
        "validation_strong"
        if promotion_readiness == "ready"
        else "validation_conditional"
        if promotion_readiness == "conditional"
        else "validation_not_ready"
    )
    demotion_reason = None if promotion_readiness == "ready" else ";".join(blockers) or "insufficient_validation"

    return {
        "schema_version": "promotion_decision_support.v1",
        "generated_at": timestamp.isoformat(),
        "scope_type": scope_type,
        "scope_id": scope_id,
        "current_probability_mode": current_probability_mode,
        "promotion_readiness": promotion_readiness,
        "promotion_reason": promotion_reason,
        "demotion_reason": demotion_reason,
        "blocking_factors": blockers,
        "validation_summary_ref": validation_summary.get("validation_summary_ref")
        or f"validation_summary.{scope_type}.{scope_id}",
        "policy_refs": policy_refs,
    }


def _to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
