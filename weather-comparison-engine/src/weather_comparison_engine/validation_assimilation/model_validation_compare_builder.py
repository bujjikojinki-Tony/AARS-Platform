from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_model_validation_compare(
    *,
    scope_type: str,
    scope_id: str,
    validation_report: dict[str, Any] | None = None,
    coverage_summary: dict[str, Any] | None = None,
    policy_refs: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict:
    timestamp = now or datetime.now(timezone.utc)
    validation_report = validation_report or {}
    coverage_summary = coverage_summary or {}
    policy_refs = policy_refs or {}

    current_model = str(validation_report.get("model_id") or "heuristic_shadow_probability_v1")
    candidate_models = _unique(
        [
            current_model,
            str(validation_report.get("model_type") or "probability_shadow"),
            "market_probability_baseline",
        ]
    )
    candidate_source_stacks = _build_source_stacks(validation_report, coverage_summary)
    validation_scores = {
        candidate_models[0]: _to_float(validation_report.get("validation_metrics", {}).get("brier_score")),
        candidate_models[1] if len(candidate_models) > 1 else "baseline": _to_float(
            validation_report.get("validation_metrics", {}).get("market_baseline_brier_score")
        ),
    }
    coverage_scores = {
        "label_coverage": _to_float(coverage_summary.get("label_coverage")),
        "source_coverage": _to_float(coverage_summary.get("source_coverage")),
        "normalization_consistency": _to_float(coverage_summary.get("normalization_consistency")),
    }
    freshness_reliability_scores = {
        "validation_freshness": _to_float(coverage_summary.get("freshness_reliability")),
        "source_precision_reliability": _to_float(coverage_summary.get("source_precision_reliability")),
    }
    selected_best_model = candidate_models[0]
    selected_best_source_stack = candidate_source_stacks[0] if candidate_source_stacks else []
    selected_best_model_reason = validation_report.get("promotion_reason") or "validation_report_current_model"

    return {
        "schema_version": "model_validation_compare.v1",
        "generated_at": timestamp.isoformat(),
        "scope_type": scope_type,
        "scope_id": scope_id,
        "candidate_models": candidate_models,
        "candidate_source_stacks": candidate_source_stacks,
        "validation_scores": validation_scores,
        "coverage_scores": coverage_scores,
        "freshness_reliability_scores": freshness_reliability_scores,
        "selected_best_model": selected_best_model,
        "selected_best_source_stack": selected_best_source_stack,
        "selected_best_model_reason": selected_best_model_reason,
        "policy_refs": policy_refs,
    }


def _build_source_stacks(validation_report: dict[str, Any], coverage_summary: dict[str, Any]) -> list[list[str]]:
    family_support = validation_report.get("family_rollout_summary") or {}
    stacks = [
        ["feature_store", "label_store", "validation_report"],
        ["forecast_snapshot", "observation_snapshot", "comparison_point"],
    ]
    if family_support:
        stacks.append(
            [
                str(family_support.get("market_family") or "family_support"),
                str(family_support.get("coverage_status") or "validation_support"),
            ]
        )
    if coverage_summary:
        stacks.append(
            [
                "coverage_summary",
                str(coverage_summary.get("coverage_status") or "coverage"),
            ]
        )
    return stacks


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
