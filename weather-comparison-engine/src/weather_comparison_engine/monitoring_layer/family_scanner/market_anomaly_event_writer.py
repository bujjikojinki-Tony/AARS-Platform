from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def build_market_anomaly_event(
    *,
    feature_row: dict,
    threshold_policy_version: str = "v1",
    source_policy_status: dict | None = None,
    now: datetime | None = None,
) -> dict:
    timestamp = now or datetime.now(timezone.utc)
    anomaly_score = _score(feature_row)
    intervention_like_score = _to_float(feature_row.get("intervention_like_score")) or 0.0
    signals = [signal for signal, active in _signals(feature_row).items() if active]
    source_policy_status = source_policy_status or {}
    source_policy_overall = str(source_policy_status.get("overall_status") or "unknown").lower()
    governance_reason = (
        "source_policy_blocked"
        if source_policy_overall == "blocked"
        else "source_policy_degraded"
        if source_policy_overall in {"degraded", "warning"}
        else "source_policy_healthy"
    )
    recommended_operator_action = "review_market_now" if anomaly_score >= 0.7 else "watch_market"
    if source_policy_overall == "blocked":
        recommended_operator_action = "review_source_policy_contract"
    elif source_policy_overall in {"degraded", "warning"} and recommended_operator_action == "watch_market":
        recommended_operator_action = "refresh_pipeline_inputs"
    return {
        "schema_version": "market_anomaly_event.v1",
        "event_id": f"anomaly_{feature_row.get('market_id')}_{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}",
        "market_id": str(feature_row.get("market_id") or ""),
        "market_family": str(feature_row.get("market_family") or "-"),
        "anomaly_score": anomaly_score,
        "intervention_like_score": round(intervention_like_score, 4),
        "anomaly_bucket": str(feature_row.get("anomaly_bucket") or _anomaly_bucket(anomaly_score)),
        "market_probability": feature_row.get("market_probability"),
        "fair_value": feature_row.get("fair_value"),
        "signals": signals,
        "primary_reason": _primary_reason(feature_row, source_policy_overall=source_policy_overall),
        "recommended_operator_action": recommended_operator_action,
        "generated_at": timestamp.isoformat(),
        "indicator_version": "v1",
        "threshold_policy_version": threshold_policy_version,
        "input_mode": "canonical_only",
        "source_policy": {
            "schema_version": str(source_policy_status.get("schema_version") or "source_policy_status.v1"),
            "overall_status": source_policy_overall,
            "fresh_count": int((source_policy_status.get("counts") or {}).get("fresh") or 0),
            "stale_count": int((source_policy_status.get("counts") or {}).get("stale") or 0),
            "unavailable_count": int((source_policy_status.get("counts") or {}).get("unavailable") or 0),
        },
        "governance_reason": governance_reason,
        "feature_breakdown": feature_row.get("feature_breakdown")
        or {
            "price_velocity": feature_row.get("price_velocity"),
            "edge_dislocation": feature_row.get("edge_dislocation"),
            "evidence_mismatch_score": feature_row.get("evidence_mismatch_score"),
            "microstructure_stress_score": feature_row.get("microstructure_stress_score"),
            "peer_rank": feature_row.get("peer_rank"),
            "peer_zscore": feature_row.get("peer_zscore"),
            "peer_outlier_flag": feature_row.get("peer_outlier_flag"),
        },
        "contract_refs": {
            "market_snapshot_ref": feature_row.get("market_snapshot_ref"),
            "market_rule_ref": feature_row.get("market_rule_ref"),
            "forecast_snapshot_ref": feature_row.get("forecast_snapshot_ref"),
            "comparison_point_ref": feature_row.get("comparison_point_ref"),
        },
        "peer_group": {
            "market_family": feature_row.get("market_family"),
            "location_name": feature_row.get("location_name"),
            "target_date": feature_row.get("target_date"),
            "variable_name": feature_row.get("variable_name"),
        },
    }


def write_market_anomaly_events(path: str | Path, events: list[dict]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fp:
        for event in events:
            fp.write(json.dumps(event, ensure_ascii=False) + "\n")
    return out


def _signals(feature_row: dict) -> dict[str, bool]:
    return {
        "price_velocity_high": _to_float(feature_row.get("price_velocity")) >= 0.05,
        "edge_dislocation": _to_float(feature_row.get("edge_dislocation")) >= 0.1,
        "evidence_mismatch": bool(feature_row.get("evidence_mismatch")),
        "spread_stress": _to_float(feature_row.get("microstructure_stress_score")) >= 0.7,
        "peer_outlier": bool(feature_row.get("peer_outlier_flag")),
    }


def _score(feature_row: dict) -> float:
    score = (
        min(1.0, (_to_float(feature_row.get("price_velocity")) or 0.0) * 5.0) * 0.25
        + min(1.0, (_to_float(feature_row.get("edge_dislocation")) or 0.0) * 5.0) * 0.25
        + (0.2 if feature_row.get("evidence_mismatch") else 0.0)
        + min(1.0, (_to_float(feature_row.get("microstructure_stress_score")) or 0.0)) * 0.2
        + min(1.0, abs(_to_float(feature_row.get("peer_zscore")) or 0.0) / 3.0) * 0.1
    )
    return round(min(1.0, score), 4)


def _primary_reason(feature_row: dict, *, source_policy_overall: str = "unknown") -> str:
    if feature_row.get("evidence_mismatch"):
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


def _anomaly_bucket(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def _to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
