from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from weather_comparison_engine.governance import normalize_measurement


def build_market_alert_event(
    *,
    market_id: str,
    observation_snapshot: dict,
    forecast_snapshot: dict,
    market_rule: dict,
    comparison_point: dict | None = None,
    previous_observation_snapshot: dict | None = None,
    threshold_policy: dict | None = None,
    source_policy_status: dict | None = None,
    now: datetime | None = None,
) -> dict:
    timestamp = now or datetime.now(timezone.utc)
    comparison_point = comparison_point or {}
    threshold_policy = dict(threshold_policy or {})
    market_rule = _canonicalize_rule(market_rule)
    observation_snapshot = _canonicalize_snapshot(observation_snapshot, market_rule=market_rule)
    forecast_snapshot = _canonicalize_snapshot(forecast_snapshot, market_rule=market_rule)
    threshold_value = dict(threshold_policy.get("threshold_value") or {})
    threshold_cross_value = _resolve_threshold_cross_value(
        market_rule=market_rule,
        comparison_point=comparison_point,
        observation_snapshot=observation_snapshot,
        threshold_policy=threshold_policy,
    )
    if threshold_cross_value is not None:
        threshold_value.setdefault("threshold_cross_value", threshold_cross_value)
    threshold_policy["threshold_value"] = threshold_value

    from weather_comparison_engine.monitoring_layer.observation_alert_layer.alert_severity_builder import (
        build_alert_severity,
    )
    from weather_comparison_engine.monitoring_layer.observation_alert_layer.forecast_divergence_detector import (
        build_forecast_divergence_result,
    )
    from weather_comparison_engine.monitoring_layer.observation_alert_layer.market_reaction_gap_detector import (
        build_market_reaction_gap_result,
    )
    from weather_comparison_engine.monitoring_layer.observation_alert_layer.observation_shock_detector import (
        build_observation_shock_result,
    )
    from weather_comparison_engine.monitoring_layer.observation_alert_layer.source_risk_evaluator import (
        build_source_risk_result,
    )

    observation_shock = build_observation_shock_result(
        observation_snapshot=observation_snapshot,
        previous_observation_snapshot=previous_observation_snapshot,
        threshold_policy=threshold_policy,
        source_match_grade=market_rule.get("source_match_grade"),
    )
    forecast_divergence = build_forecast_divergence_result(
        observation_snapshot=observation_snapshot,
        forecast_snapshot=forecast_snapshot,
        market_rule=market_rule,
        source_confidence=forecast_snapshot.get("source_confidence"),
    )
    market_reaction_gap = build_market_reaction_gap_result(
        market_snapshot={**observation_snapshot, **forecast_snapshot, **comparison_point, "market_id": market_id},
        probability_state=comparison_point.get("probability_state") or comparison_point,
        comparison_point=comparison_point,
    )
    source_risk = build_source_risk_result(market_rule=market_rule, forecast_snapshot=forecast_snapshot)
    severity = build_alert_severity(
        observation_shock=observation_shock,
        forecast_divergence=forecast_divergence,
        market_reaction_gap=market_reaction_gap,
        source_risk=source_risk,
        source_policy_status=source_policy_status,
        market_rule=market_rule,
        market_snapshot=observation_snapshot,
        forecast_snapshot=forecast_snapshot,
    )

    source_policy_status = source_policy_status or {}
    source_policy_overall = str(source_policy_status.get("overall_status") or "unknown")

    return {
        "schema_version": "market_alert_event.v1",
        "event_id": f"alert_{market_id}_{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}",
        "market_id": str(market_id),
        "market_family": str(market_rule.get("market_family") or observation_snapshot.get("market_family") or "-"),
        "event_type": "observation_alert",
        "severity": severity["severity"],
        "primary_reason": severity["primary_reason"],
        "recommended_operator_action": severity["recommended_operator_action"],
        "alert_score": severity["alert_score"],
        "observation_value": observation_snapshot.get("observation_canonical_value")
        or observation_snapshot.get("observation_value")
        or observation_snapshot.get("observed_temp_c"),
        "forecast_value": forecast_snapshot.get("forecast_canonical_value")
        or forecast_snapshot.get("forecast_value")
        or forecast_snapshot.get("value"),
        "observation_canonical_value": observation_snapshot.get("observation_canonical_value"),
        "forecast_canonical_value": forecast_snapshot.get("forecast_canonical_value"),
        "observation_display_value": observation_snapshot.get("observation_display_value")
        or observation_snapshot.get("observation_value"),
        "forecast_display_value": forecast_snapshot.get("forecast_display_value")
        or forecast_snapshot.get("forecast_value"),
        "market_probability": comparison_point.get("market_probability") or observation_snapshot.get("market_probability"),
        "fair_value": comparison_point.get("fair_value") or comparison_point.get("model_value"),
        "source_match_grade": market_rule.get("source_match_grade") or "unknown",
        "freshness_status": market_rule.get("freshness_status") or forecast_snapshot.get("freshness_status") or "unknown",
        "generated_at": timestamp.isoformat(),
        "indicator_version": "v1",
        "threshold_policy_version": str((threshold_policy or {}).get("version") or "v1"),
        "source_policy": {
            "schema_version": str(source_policy_status.get("schema_version") or "source_policy_status.v1"),
            "overall_status": source_policy_overall,
            "fresh_count": int((source_policy_status.get("counts") or {}).get("fresh") or 0),
            "stale_count": int((source_policy_status.get("counts") or {}).get("stale") or 0),
            "unavailable_count": int((source_policy_status.get("counts") or {}).get("unavailable") or 0),
            "problem_sources": (source_policy_status.get("problem_sources") or [])[:3],
        },
        "governance_reason": (
            "source_policy_blocked"
            if source_policy_overall == "blocked"
            else "source_policy_degraded"
            if source_policy_overall in {"degraded", "warning"}
            else "source_policy_healthy"
        ),
        "contract_refs": {
            "market_snapshot_ref": observation_snapshot.get("market_snapshot_ref"),
            "market_rule_ref": market_rule.get("market_rule_ref"),
            "forecast_snapshot_ref": forecast_snapshot.get("forecast_snapshot_ref"),
            "observation_snapshot_ref": observation_snapshot.get("observation_snapshot_ref"),
            "comparison_point_ref": comparison_point.get("comparison_point_ref"),
        },
        "signals": {
            "observation_shock": observation_shock,
            "forecast_divergence": forecast_divergence,
            "market_reaction_gap": market_reaction_gap,
            "source_risk": source_risk,
            "threshold_cross_value": threshold_cross_value,
            "input_mode": "canonical_only",
        },
    }


def _resolve_threshold_cross_value(
    *,
    market_rule: dict,
    comparison_point: dict,
    observation_snapshot: dict,
    threshold_policy: dict,
) -> float | None:
    for candidate in (
        threshold_policy.get("threshold_value", {}).get("threshold_cross_value"),
        market_rule.get("threshold_cross_value"),
        comparison_point.get("threshold_cross_value"),
        comparison_point.get("market_band"),
        observation_snapshot.get("threshold_cross_value"),
    ):
        value = _to_float(candidate)
        if value is not None:
            return value
    return None


def _canonicalize_rule(market_rule: dict) -> dict:
    market_rule = dict(market_rule or {})
    return market_rule


def _canonicalize_snapshot(snapshot: dict, *, market_rule: dict) -> dict:
    snapshot = dict(snapshot or {})
    family = str(market_rule.get("market_family") or snapshot.get("market_family") or "").strip()
    variable_name = str(market_rule.get("variable_name") or snapshot.get("variable_name") or "").strip()
    raw_unit = snapshot.get("raw_unit") or snapshot.get("unit")
    band_scheme = snapshot.get("band_scheme") or market_rule.get("band_scheme")
    normalized = normalize_measurement(
        {
            "raw_value": snapshot.get("raw_value")
            or snapshot.get("canonical_value")
            or snapshot.get("display_value")
            or snapshot.get("observation_value")
            or snapshot.get("forecast_value")
            or snapshot.get("value"),
            "raw_unit": raw_unit,
        },
        family=family,
        variable_name=variable_name,
        raw_unit=str(raw_unit) if raw_unit not in (None, "") else None,
        band_scheme=str(band_scheme) if band_scheme not in (None, "") else None,
    )
    snapshot.setdefault("raw_value", normalized.get("raw_value"))
    snapshot.setdefault("raw_unit", normalized.get("raw_unit"))
    snapshot.setdefault("canonical_value", normalized.get("canonical_value"))
    snapshot.setdefault("canonical_unit", normalized.get("canonical_unit"))
    snapshot.setdefault("display_value", normalized.get("display_value"))
    snapshot.setdefault("display_unit", normalized.get("display_unit"))
    snapshot.setdefault("precision_policy_ref", normalized.get("precision_policy_ref"))
    snapshot.setdefault("rounding_policy_ref", normalized.get("rounding_policy_ref"))
    snapshot.setdefault("band_mapping_policy_ref", normalized.get("band_mapping_policy_ref"))
    snapshot.setdefault("normalization_version", normalized.get("normalization_version"))
    return snapshot


def _to_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def write_market_alert_event(path: str | Path, event: dict) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(event, ensure_ascii=False) + "\n")
    return out
