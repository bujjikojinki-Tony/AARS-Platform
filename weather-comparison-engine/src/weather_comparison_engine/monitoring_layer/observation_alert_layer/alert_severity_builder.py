from __future__ import annotations


def build_alert_severity(
    *,
    observation_shock: dict | None = None,
    forecast_divergence: dict | None = None,
    market_reaction_gap: dict | None = None,
    source_risk: dict | None = None,
    source_policy_status: dict | None = None,
    market_rule: dict | None = None,
    market_snapshot: dict | None = None,
    forecast_snapshot: dict | None = None,
) -> dict:
    observation_shock = observation_shock or {}
    forecast_divergence = forecast_divergence or {}
    market_reaction_gap = market_reaction_gap or {}
    source_risk = source_risk or {}
    source_policy_status = source_policy_status or {}

    source_match_risk = str(source_risk.get("source_match_risk") or "high")
    freshness_risk = str(source_risk.get("freshness_risk") or "high")
    source_policy_overall = str(source_policy_status.get("overall_status") or "unknown").lower()
    source_policy_reason = _source_policy_reason(source_policy_overall)

    shock_hit = bool(observation_shock.get("threshold_cross_event"))
    divergence_hit = _to_float(forecast_divergence.get("forecast_divergence_score")) or 0.0
    lag_score = _to_float(market_reaction_gap.get("reaction_lag_score")) or 0.0
    fair_value_gap = abs(_to_float(market_reaction_gap.get("fair_value_gap")) or 0.0)

    if shock_hit and lag_score > 0 and source_match_risk == "low" and freshness_risk == "low":
        severity = "red"
        primary_reason = "threshold_cross_with_fresh_exact_station_lag"
        action = "review_market_now"
        score = 1.0
    elif divergence_hit >= 0.5 or fair_value_gap >= 0.15 or lag_score >= 0.5:
        severity = "amber"
        primary_reason = "strong_divergence_or_reaction_gap"
        action = "review_market_now"
        score = 0.75
    elif shock_hit or divergence_hit >= 0.2 or fair_value_gap >= 0.05 or source_match_risk != "low":
        severity = "watch"
        primary_reason = "signal_present_or_source_risk"
        action = "watch_and_review"
        score = 0.45
    else:
        severity = "info"
        primary_reason = "state_change_only"
        action = "log_only"
        score = 0.1

    if source_policy_reason:
        if primary_reason == "state_change_only":
            primary_reason = source_policy_reason
        elif source_policy_reason not in primary_reason:
            primary_reason = f"{primary_reason}+{source_policy_reason}"
        if source_policy_overall == "blocked":
            action = "review_source_policy_contract"
        elif source_policy_overall == "degraded" and action in {"log_only", "watch_and_review"}:
            action = "refresh_pipeline_inputs"

    return {
        "severity": severity,
        "recommended_operator_action": action,
        "alert_score": round(score, 3),
        "primary_reason": primary_reason,
    }


def _to_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _source_policy_reason(source_policy_overall: str) -> str | None:
    if source_policy_overall == "blocked":
        return "source_policy_blocked"
    if source_policy_overall in {"degraded", "warning"}:
        return "source_policy_degraded"
    return None
