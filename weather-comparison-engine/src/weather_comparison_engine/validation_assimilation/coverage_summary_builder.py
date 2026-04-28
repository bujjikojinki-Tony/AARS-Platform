from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_coverage_summary(
    *,
    scope_type: str,
    scope_id: str,
    validation_report: dict[str, Any] | None = None,
    label_coverage_report: dict[str, Any] | None = None,
    feature_store_summary: dict[str, Any] | None = None,
    upstream_refs: dict[str, Any] | None = None,
    policy_refs: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict:
    timestamp = now or datetime.now(timezone.utc)
    validation_report = validation_report or {}
    label_coverage_report = label_coverage_report or {}
    feature_store_summary = feature_store_summary or {}
    policy_refs = policy_refs or {}
    upstream_refs = upstream_refs or {}

    source_coverage = _to_float(
        feature_store_summary.get("source_policy_coverage")
        or validation_report.get("governance_summary", {}).get("source_policy_coverage")
        or 0.0
    )
    label_coverage = _to_float(
        label_coverage_report.get("labeled_ratio")
        or validation_report.get("governance_summary", {}).get("canonical_ratio")
        or 0.0
    )
    official_label_coverage = _to_float(label_coverage_report.get("official_record_coverage"))
    forecast_coverage = _to_float(feature_store_summary.get("forecast_coverage"))
    observation_coverage = _to_float(feature_store_summary.get("observation_coverage"))
    freshness_reliability = _to_float(
        feature_store_summary.get("freshness_reliability")
        or validation_report.get("validation_metrics", {}).get("market_baseline_brier_score")
    )
    source_precision_reliability = _to_float(
        feature_store_summary.get("source_precision_reliability")
        or validation_report.get("resolver_quality", {}).get("match_rate")
    )

    coverage_components = {
        "label_coverage": label_coverage,
        "official_label_coverage": official_label_coverage,
        "source_coverage": source_coverage,
        "forecast_coverage": forecast_coverage,
        "observation_coverage": observation_coverage,
        "freshness_reliability": freshness_reliability,
        "source_precision_reliability": source_precision_reliability,
    }
    status = "healthy"
    if label_coverage <= 0.0 or source_coverage <= 0.0:
        status = "insufficient"
    elif label_coverage < 0.5 or source_coverage < 0.5:
        status = "weak"
    elif label_coverage < 0.75 or source_coverage < 0.75:
        status = "moderate"

    return {
        "schema_version": "coverage_summary.v1",
        "generated_at": timestamp.isoformat(),
        "scope_type": scope_type,
        "scope_id": scope_id,
        "label_coverage": label_coverage,
        "official_label_coverage": official_label_coverage,
        "source_coverage": source_coverage,
        "forecast_coverage": forecast_coverage,
        "observation_coverage": observation_coverage,
        "freshness_reliability": freshness_reliability,
        "source_precision_reliability": source_precision_reliability,
        "coverage_components": coverage_components,
        "coverage_status": status,
        "upstream_refs": upstream_refs,
        "policy_refs": policy_refs,
    }


def _to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
