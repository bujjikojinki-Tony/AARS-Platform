from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from weather_comparison_engine.opportunity_board.best_model_recommender import recommend_best_model_details
from weather_comparison_engine.opportunity_board.difficulty_score_builder import build_difficulty_score_details
from weather_comparison_engine.opportunity_board.opportunity_score_builder import build_opportunity_score_details
from weather_comparison_engine.opportunity_board.recommended_action_mapper import map_recommended_action


def build_opportunity_row(
    *,
    city: str,
    market_family: str,
    rows: list[dict],
    context: dict | None = None,
) -> dict:
    context = context or {}
    market_ids = [str(row.get("market_id") or "") for row in rows if str(row.get("market_id") or "").strip()]
    latest_row = _latest_row(rows)
    alert_index = context.get("alert_index") or {}
    anomaly_index = context.get("anomaly_index") or {}
    comparison_index = context.get("comparison_index") or {}
    gate_index = context.get("gate_index") or {}

    alert_payloads = [alert_index.get(market_id) for market_id in market_ids if market_id in alert_index]
    anomaly_payloads = [anomaly_index.get(market_id) for market_id in market_ids if market_id in anomaly_index]
    comparison_payloads = [comparison_index.get(market_id) for market_id in market_ids if market_id in comparison_index]
    gate_payloads = [gate_index.get(market_id) for market_id in market_ids if market_id in gate_index]

    alert_count = len(alert_payloads)
    anomaly_count = len(anomaly_payloads)
    latest_alert = _latest_by_time(alert_payloads, key="generated_at")
    latest_anomaly = _latest_by_time(anomaly_payloads, key="generated_at")
    latest_comparison = _latest_by_time(comparison_payloads, key="timestamp")
    latest_gate = _latest_by_time(gate_payloads, key="generated_at")

    source_precision_score = _source_precision_score(latest_row, context)
    freshness_status = _freshness_status(latest_row, latest_gate, context)
    opportunity_details = build_opportunity_score_details(
        {
            **latest_row,
            "alert_count": alert_count,
            "anomaly_count": anomaly_count,
            "freshness_status": freshness_status,
        },
        context,
    )
    difficulty_details = build_difficulty_score_details(
        {
            **latest_row,
            "freshness_status": freshness_status,
        },
        context,
    )
    best_model_details = recommend_best_model_details(
        {
            **latest_row,
            "market_question": latest_row.get("market_question") or context.get("market_question") or "",
        },
        context,
    )

    opportunity_score = opportunity_details["opportunity_score"]
    opportunity_reason = opportunity_details["opportunity_reason"]
    difficulty_score = difficulty_details["difficulty_score"]
    difficulty_label = difficulty_details["difficulty_label"]
    difficulty_reason = difficulty_details["difficulty_reason"]
    best_model = best_model_details["best_model"]
    best_source_stack = best_model_details["best_source_stack"]
    best_model_reason = best_model_details["best_model_reason"]

    opportunity_rank = int(context.get("opportunity_rank") or 0)
    latest_alert_severity = str((latest_alert or {}).get("severity") or "-")
    latest_anomaly_score = _to_float((latest_anomaly or {}).get("anomaly_score"))
    gate_risk_summary = _gate_risk_summary(latest_gate, freshness_status)
    action_details = map_recommended_action(
        latest_alert=latest_alert,
        latest_anomaly=latest_anomaly,
        latest_gate=latest_gate,
        freshness_status=freshness_status,
        difficulty_score=difficulty_score,
        has_market_ids=bool(market_ids),
        seeded=bool(latest_row.get("seeded_from_manual_research")),
        context=context,
    )
    recommended_action = action_details["recommended_action"]
    upstream_refs = {
        "market_ids": market_ids,
        "comparison_refs": _comparison_refs(comparison_payloads),
        "alert_refs": _event_refs(alert_payloads, key="event_id"),
        "anomaly_refs": _event_refs(anomaly_payloads, key="event_id"),
        "gate_refs": _event_refs(gate_payloads, key="market_id"),
    }

    return {
        "row_id": f"{city}.{market_family}",
        "city": city,
        "country": _country_from_row(latest_row),
        "market_family": market_family,
        "active_market_count": len(rows),
        "opportunity_score": opportunity_score,
        "opportunity_rank": opportunity_rank,
        "difficulty_score": difficulty_score,
        "difficulty_label": difficulty_label,
        "best_model": best_model,
        "best_source_stack": best_source_stack,
        "source_precision_score": source_precision_score,
        "freshness_status": freshness_status,
        "alert_count": alert_count,
        "latest_alert_severity": latest_alert_severity,
        "anomaly_count": anomaly_count,
        "latest_anomaly_score": latest_anomaly_score,
        "gate_risk_summary": gate_risk_summary,
        "recommended_action": recommended_action,
        "opportunity_reason": opportunity_reason,
        "difficulty_reason": difficulty_reason,
        "best_model_reason": best_model_reason,
        "opportunity_components": opportunity_details["opportunity_components"],
        "difficulty_components": difficulty_details["difficulty_components"],
        "best_model_components": best_model_details["best_model_components"],
        "opportunity_policy_ref": opportunity_details.get("opportunity_policy_ref"),
        "scoring_policy_ref": opportunity_details.get("scoring_policy_ref"),
        "difficulty_policy_ref": difficulty_details.get("difficulty_policy_ref"),
        "model_recommendation_policy_ref": best_model_details.get("model_recommendation_policy_ref"),
        "action_mapping_policy_ref": action_details.get("action_mapping_policy_ref"),
        "freshness_mapping_policy_ref": opportunity_details.get("freshness_mapping_policy_ref"),
        "source_precision_policy_ref": opportunity_details.get("source_precision_policy_ref"),
        "seed_id": latest_row.get("seed_id"),
        "seeded_from_manual_research": bool(latest_row.get("seeded_from_manual_research")),
        "seed_status": latest_row.get("seed_status"),
        "source_origin": latest_row.get("source_origin"),
        "manual_confidence": latest_row.get("manual_confidence"),
        "seed_notes": latest_row.get("seed_notes"),
        "superseded_by_system_score": bool(latest_row.get("superseded_by_system_score")),
        "upstream_refs": upstream_refs,
        "latest_context": {
            "market_id": latest_row.get("market_id"),
            "comparison_status": latest_row.get("comparison_status"),
            "comparison_reason": latest_row.get("comparison_reason"),
            "action_hint": latest_row.get("action_hint"),
        },
    }


def _latest_row(rows: list[dict]) -> dict:
    if not rows:
        return {}
    if len(rows) == 1:
        return rows[0]
    ranked = sorted(rows, key=lambda row: str(row.get("timestamp") or row.get("updated_at") or ""), reverse=True)
    return ranked[0] if ranked else {}


def _source_precision_score(row: dict, context: dict | None = None) -> float:
    policy = ((context or {}).get("opportunity_policy_bundle") or {}).get("source_precision_policy") or {}
    grade = str(row.get("source_match_grade") or "").lower()
    official_vs_proxy = str(row.get("official_vs_proxy_source") or "").lower()
    resolver_confidence = _to_float(row.get("resolver_confidence")) or 0.0
    combination_scores = policy.get("combination_scores") or {}
    combination_key = f"{grade}:{official_vs_proxy}"
    if combination_key in combination_scores:
        return max(0.0, min(1.0, round(float(combination_scores.get(combination_key) or 0.0), 4)))
    mapping = {
        "exact_station": 0.98,
        "family_exact": 0.82,
        "family_only": 0.58,
        "unmatched": 0.28,
        "": 0.35,
    }
    if policy.get("match_grade_scores"):
        mapping = policy.get("match_grade_scores") or mapping
    base = float(mapping.get(grade, mapping.get("unknown", 0.45)) or 0.0)
    adjustments = policy.get("officialness_adjustments") or {}
    base += float(adjustments.get(official_vs_proxy, 0.0) or 0.0)
    base += min(max(resolver_confidence, 0.0), 1.0) * float(policy.get("resolver_confidence_weight", 0.0) or 0.0)
    return max(0.0, min(1.0, round(base, 4)))


def _freshness_status(latest_row: dict, latest_gate: dict, context: dict) -> str:
    candidate = str(
        latest_gate.get("freshness_gate")
        or latest_row.get("freshness_status")
        or context.get("freshness_status")
        or "unknown"
    ).lower()
    if candidate in {"pass", "fresh", "healthy"}:
        return "fresh"
    if candidate == "seed_prior":
        return "seed_prior"
    if candidate in {"warning", "warm"}:
        return "warm"
    if candidate in {"blocked", "stale", "unavailable"}:
        return candidate
    return "unknown"


def _gate_risk_summary(latest_gate: dict, freshness_status: str) -> str:
    if not latest_gate:
        return "summary_unavailable"
    if str(latest_gate.get("execution_gate") or "").lower() != "pass":
        return "manual_advisory_only"
    if freshness_status in {"blocked", "stale", "unavailable"}:
        return "refresh_pipeline_inputs"
    return "review_and_watch"


def _comparison_refs(payloads: list[dict]) -> list[str]:
    refs = []
    for payload in payloads:
        token = str(payload.get("timestamp") or payload.get("market_snapshot_ref") or "").strip()
        if token and token not in refs:
            refs.append(token)
    return refs


def _event_refs(payloads: list[dict], *, key: str) -> list[str]:
    refs = []
    for payload in payloads:
        token = str(payload.get(key) or payload.get("generated_at") or "").strip()
        if token and token not in refs:
            refs.append(token)
    return refs


def _country_from_row(row: dict) -> str:
    text = str(row.get("country") or row.get("location_country") or "").strip()
    return text or "-"


def _latest_by_time(payloads: list[dict], *, key: str) -> dict:
    if not payloads:
        return {}
    ranked = sorted(payloads, key=lambda item: str(item.get(key) or ""), reverse=True)
    return ranked[0] if ranked else {}


def _to_float(value: object) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except Exception:
        return None
