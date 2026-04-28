from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from weather_comparison_engine.advanced_anomaly.intervention_like_scorer import score_intervention_like
from weather_comparison_engine.advanced_anomaly.microstructure_stress_builder import build_microstructure_stress
from weather_comparison_engine.advanced_anomaly.peer_relative_anomaly_builder import build_peer_relative_anomaly
from weather_comparison_engine.monitoring_layer.family_scanner.anomaly_feature_builder import build_anomaly_features


def build_market_anomaly_event_v2(
    *,
    feature_row: dict[str, Any],
    source_policy_status: dict[str, Any] | None = None,
    policy_refs: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict:
    timestamp = now or datetime.now(timezone.utc)
    source_policy_status = source_policy_status or {}
    policy_refs = policy_refs or {}
    anomaly_score = _score(feature_row)
    signals = _signals(feature_row)
    microstructure = build_microstructure_stress(market_row=feature_row)
    peer = build_peer_relative_anomaly(market_row=feature_row, peer_rows=feature_row.get("peer_rows") or [])
    intervention = score_intervention_like(
        price_velocity_score=_to_float(feature_row.get("price_velocity")),
        microstructure_stress_score=_to_float(feature_row.get("microstructure_stress_score") or microstructure["microstructure_stress_score"]),
        evidence_mismatch_score=_to_float(feature_row.get("evidence_mismatch_score")),
        peer_relative_anomaly_score=_to_float(feature_row.get("peer_relative_anomaly_score") or peer["peer_relative_anomaly_score"]),
        evidence_support_quality=_to_float(feature_row.get("evidence_support_quality") or 1.0),
    )
    source_policy_overall = str(source_policy_status.get("overall_status") or "unknown").lower()
    recommended_operator_action = "review_market_now" if anomaly_score >= 0.7 else "watch_market"
    if source_policy_overall == "blocked":
        recommended_operator_action = "review_source_policy_contract"
    elif source_policy_overall in {"degraded", "warning"} and recommended_operator_action == "watch_market":
        recommended_operator_action = "refresh_pipeline_inputs"

    return {
        "schema_version": "market_anomaly_event.v2",
        "event_id": f"anomaly_v2_{feature_row.get('market_id')}_{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}",
        "generated_at": timestamp.isoformat(),
        "market_id": str(feature_row.get("market_id") or ""),
        "market_family": str(feature_row.get("market_family") or "-"),
        "anomaly_score": anomaly_score,
        "price_velocity_score": round(_to_float(feature_row.get("price_velocity")), 4),
        "edge_dislocation_score": round(_to_float(feature_row.get("edge_dislocation")), 4),
        "evidence_mismatch_score": round(_to_float(feature_row.get("evidence_mismatch_score")), 4),
        "microstructure_stress_score": microstructure["microstructure_stress_score"],
        "peer_relative_anomaly_score": peer["peer_relative_anomaly_score"],
        "intervention_like_score": intervention["intervention_like_score"],
        "intervention_like_flag": intervention["intervention_like_flag"],
        "signals": signals,
        "primary_reason": _primary_reason(feature_row, source_policy_overall=source_policy_overall),
        "recommended_operator_action": recommended_operator_action,
        "policy_refs": {
            "anomaly_policy_ref": policy_refs.get("anomaly_policy_ref") or "threshold_policy.intervention_like_score.default.v1",
            "source_policy_ref": policy_refs.get("source_policy_ref") or source_policy_status.get("schema_version") or "source_policy_status.v1",
        },
        "upstream_refs": {
            "market_snapshot_ref": feature_row.get("market_snapshot_ref"),
            "market_rule_ref": feature_row.get("market_rule_ref"),
            "forecast_snapshot_ref": feature_row.get("forecast_snapshot_ref"),
            "observation_snapshot_ref": feature_row.get("observation_snapshot_ref"),
            "comparison_point_ref": feature_row.get("comparison_point_ref"),
        },
        "feature_breakdown": {
            "price_velocity": round(_to_float(feature_row.get("price_velocity")), 4),
            "edge_dislocation": round(_to_float(feature_row.get("edge_dislocation")), 4),
            "evidence_mismatch_score": round(_to_float(feature_row.get("evidence_mismatch_score")), 4),
            "microstructure_stress_score": microstructure["microstructure_stress_score"],
            "peer_rank": peer["peer_rank"],
            "peer_zscore": peer["peer_zscore"],
            "peer_outlier_flag": peer["peer_outlier_flag"],
        },
        "peer_group": {
            "market_family": feature_row.get("market_family"),
            "location_name": feature_row.get("location_name"),
            "target_date": feature_row.get("target_date"),
            "variable_name": feature_row.get("variable_name"),
        },
    }


def build_family_anomaly_summary_v1(
    *,
    market_family: str,
    feature_rows: list[dict[str, Any]],
    policy_refs: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict:
    timestamp = now or datetime.now(timezone.utc)
    policy_refs = policy_refs or {}
    family_rows = [row for row in feature_rows if str(row.get("market_family") or "") == str(market_family)]
    top_anomalies = sorted(
        family_rows,
        key=lambda row: (-_to_float(row.get("intervention_like_score")), str(row.get("market_id") or "")),
    )[:10]
    return {
        "schema_version": "family_anomaly_summary.v1",
        "generated_at": timestamp.isoformat(),
        "market_family": market_family,
        "scanned_market_count": len(family_rows),
        "high_anomaly_count": sum(1 for row in family_rows if _to_float(row.get("intervention_like_score")) >= 0.8),
        "high_intervention_like_count": sum(1 for row in family_rows if _to_float(row.get("intervention_like_score")) >= 0.8),
        "top_anomalies": top_anomalies,
        "family_risk_summary": _family_risk_summary(family_rows),
        "policy_refs": policy_refs,
    }


def build_advanced_anomaly_outputs(
    *,
    market_rows: list[dict[str, Any]],
    comparison_history: list[dict[str, Any]],
    probability_states: dict[str, dict[str, Any]] | None = None,
    source_policy_status: dict[str, Any] | None = None,
    policy_refs: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict:
    probability_states = probability_states or {}
    source_policy_status = source_policy_status or {}
    policy_refs = policy_refs or {}
    timestamp = now or datetime.now(timezone.utc)
    market_rows = [row for row in market_rows if isinstance(row, dict)]
    comparison_history = [row for row in comparison_history if isinstance(row, dict)]

    feature_rows = [
        build_anomaly_features(
            market_row=row,
            comparison_history=comparison_history,
            probability_state=probability_states.get(str(row.get("market_id") or "")),
        )
        for row in market_rows
    ]
    market_events = [
        build_market_anomaly_event_v2(
            feature_row=feature_row,
            source_policy_status=source_policy_status,
            policy_refs=policy_refs,
            now=timestamp,
        )
        for feature_row in feature_rows
    ]
    family_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for feature_row in feature_rows:
        family_groups[str(feature_row.get("market_family") or "-")].append(feature_row)
    family_summaries = [
        build_family_anomaly_summary_v1(
            market_family=family,
            feature_rows=rows,
            policy_refs=policy_refs,
            now=timestamp,
        )
        for family, rows in sorted(family_groups.items())
    ]
    return {
        "generated_at": timestamp.isoformat(),
        "schema_version": "advanced_anomaly_outputs.v1",
        "feature_rows": feature_rows,
        "market_events": market_events,
        "family_summaries": family_summaries,
    }


def _signals(feature_row: dict[str, Any]) -> list[str]:
    signals: list[str] = []
    if _to_float(feature_row.get("price_velocity")) >= 0.05:
        signals.append("price_velocity_high")
    if _to_float(feature_row.get("edge_dislocation")) >= 0.1:
        signals.append("edge_dislocation")
    if bool(feature_row.get("evidence_mismatch")):
        signals.append("evidence_mismatch")
    if _to_float(feature_row.get("microstructure_stress_score")) >= 0.7:
        signals.append("microstructure_stress")
    if bool(feature_row.get("peer_outlier_flag")):
        signals.append("peer_outlier")
    return signals


def _primary_reason(feature_row: dict[str, Any], *, source_policy_overall: str) -> str:
    if bool(feature_row.get("evidence_mismatch")):
        return _join_reason("evidence_mismatch", source_policy_overall)
    if _to_float(feature_row.get("edge_dislocation")) >= 0.1:
        return _join_reason("edge_dislocation", source_policy_overall)
    if _to_float(feature_row.get("price_velocity")) >= 0.05:
        return _join_reason("price_velocity_high", source_policy_overall)
    return _join_reason("family_anomaly_scan", source_policy_overall)


def _join_reason(base_reason: str, source_policy_overall: str) -> str:
    if source_policy_overall == "blocked":
        return f"{base_reason}+source_policy_blocked"
    if source_policy_overall in {"degraded", "warning"}:
        return f"{base_reason}+source_policy_degraded"
    return base_reason


def _family_risk_summary(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "no_family_anomaly_signal"
    avg_score = sum(_to_float(row.get("intervention_like_score")) for row in rows) / len(rows)
    if avg_score >= 0.8:
        return "high_family_anomaly_risk"
    if avg_score >= 0.5:
        return "moderate_family_anomaly_risk"
    return "low_family_anomaly_risk"


def _score(feature_row: dict[str, Any]) -> float:
    score = (
        min(1.0, (_to_float(feature_row.get("price_velocity")) or 0.0) * 5.0) * 0.25
        + min(1.0, (_to_float(feature_row.get("edge_dislocation")) or 0.0) * 5.0) * 0.25
        + (0.2 if feature_row.get("evidence_mismatch") else 0.0)
        + min(1.0, (_to_float(feature_row.get("microstructure_stress_score")) or 0.0)) * 0.2
        + min(1.0, abs(_to_float(feature_row.get("peer_zscore")) or 0.0) / 3.0) * 0.1
    )
    return round(min(1.0, score), 4)


def _to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
