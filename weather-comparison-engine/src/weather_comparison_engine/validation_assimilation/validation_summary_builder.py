from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_validation_summary(
    *,
    scope_type: str,
    scope_id: str,
    validation_report: dict[str, Any] | None = None,
    validation_freshness: dict[str, Any] | None = None,
    coverage_summary: dict[str, Any] | None = None,
    label_coverage_report: dict[str, Any] | None = None,
    feature_store_summary: dict[str, Any] | None = None,
    policy_refs: dict[str, Any] | None = None,
    upstream_refs: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict:
    timestamp = now or datetime.now(timezone.utc)
    validation_report = validation_report or {}
    validation_freshness = validation_freshness or {}
    coverage_summary = coverage_summary or {}
    label_coverage_report = label_coverage_report or {}
    feature_store_summary = feature_store_summary or {}
    policy_refs = policy_refs or {}
    upstream_refs = upstream_refs or {}

    freshness_status = str(validation_freshness.get("status") or "unknown").lower()
    freshness_seconds = validation_freshness.get("freshness_seconds")
    label_coverage = _to_float(
        coverage_summary.get("label_coverage")
        or label_coverage_report.get("labeled_ratio")
        or validation_report.get("governance_summary", {}).get("canonical_ratio")
    )
    source_coverage = _to_float(
        coverage_summary.get("source_coverage")
        or feature_store_summary.get("source_policy_coverage")
        or validation_report.get("governance_summary", {}).get("source_policy_coverage")
    )
    normalization_consistency = _to_float(
        validation_report.get("governance_summary", {}).get("normalization_coverage")
        or coverage_summary.get("normalization_consistency")
        or feature_store_summary.get("normalization_consistency")
    )
    family_support_level = str(
        validation_report.get("family_rollout_summary", {}).get("support_level")
        or validation_report.get("family_rollout_summary", {}).get("coverage_status")
        or "insufficient"
    )

    reasons = _build_reasons(
        validation_report=validation_report,
        validation_freshness=validation_freshness,
        coverage_summary=coverage_summary,
        label_coverage=label_coverage,
        source_coverage=source_coverage,
        normalization_consistency=normalization_consistency,
    )
    validation_status = _resolve_validation_status(
        freshness_status=freshness_status,
        label_coverage=label_coverage,
        source_coverage=source_coverage,
        normalization_consistency=normalization_consistency,
        reasons=reasons,
    )
    promotion_readiness = _resolve_promotion_readiness(validation_status, reasons)

    return {
        "schema_version": "validation_summary.v1",
        "generated_at": timestamp.isoformat(),
        "scope_type": scope_type,
        "scope_id": scope_id,
        "validation_status": validation_status,
        "validation_age": _format_age(freshness_seconds),
        "label_coverage": label_coverage,
        "source_coverage": source_coverage,
        "normalization_consistency": normalization_consistency,
        "family_support_level": family_support_level,
        "promotion_readiness": promotion_readiness,
        "reasons": reasons,
        "policy_refs": policy_refs,
        "upstream_refs": upstream_refs,
    }


def _build_reasons(
    *,
    validation_report: dict[str, Any],
    validation_freshness: dict[str, Any],
    coverage_summary: dict[str, Any],
    label_coverage: float,
    source_coverage: float,
    normalization_consistency: float,
) -> list[str]:
    reasons: list[str] = []
    freshness_status = str(validation_freshness.get("status") or "").lower()
    if freshness_status in {"warning", "blocked"}:
        reasons.append(f"freshness:{freshness_status}")
    if label_coverage < 0.5:
        reasons.append("low_label_coverage")
    if source_coverage < 0.5:
        reasons.append("low_source_coverage")
    if normalization_consistency < 0.5:
        reasons.append("low_normalization_consistency")
    blockers = validation_report.get("promotion_blockers") or validation_report.get("promotion_blockers")
    for blocker in blockers or []:
        reasons.append(str(blocker))
    if not reasons:
        reasons.append(str(coverage_summary.get("coverage_status") or "validation_ready"))
    return reasons


def _resolve_validation_status(
    *,
    freshness_status: str,
    label_coverage: float,
    source_coverage: float,
    normalization_consistency: float,
    reasons: list[str],
) -> str:
    if freshness_status in {"blocked", "missing"}:
        return "insufficient"
    if label_coverage < 0.25 or source_coverage < 0.25:
        return "insufficient"
    if label_coverage < 0.5 or source_coverage < 0.5 or normalization_consistency < 0.5:
        return "weak"
    if label_coverage < 0.75 or source_coverage < 0.75 or freshness_status == "warning":
        return "moderate"
    return "strong" if not any(reason.startswith("low_") for reason in reasons) else "moderate"


def _resolve_promotion_readiness(validation_status: str, reasons: list[str]) -> str:
    if validation_status == "strong":
        return "ready"
    if validation_status in {"moderate", "weak"} and reasons:
        return "conditional"
    return "not_ready"


def _format_age(freshness_seconds: object) -> str | None:
    if freshness_seconds is None:
        return None
    try:
        seconds = float(freshness_seconds)
    except (TypeError, ValueError):
        return None
    if seconds < 60:
        return f"{round(seconds, 1)}s"
    minutes = seconds / 60.0
    if minutes < 60:
        return f"{round(minutes, 1)}m"
    hours = minutes / 60.0
    return f"{round(hours, 1)}h"


def _to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
