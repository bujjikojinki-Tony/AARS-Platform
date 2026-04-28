from __future__ import annotations

from weather_comparison_engine.opportunity_board.opportunity_policy_loader import policy_ref


def map_recommended_action(
    *,
    latest_alert: dict | None,
    latest_anomaly: dict | None,
    latest_gate: dict | None,
    freshness_status: str,
    difficulty_score: float,
    has_market_ids: bool,
    seeded: bool,
    context: dict | None = None,
) -> dict:
    context = context or {}
    policy = (context.get("opportunity_policy_bundle") or {}).get("action_mapping_policy") or {}
    thresholds = policy.get("thresholds") or {}
    high_anomaly_score = float(thresholds.get("high_anomaly_score", 0.75) or 0.75)
    hard_difficulty_min = float(thresholds.get("hard_difficulty_min", 0.66) or 0.66)

    if seeded and not has_market_ids:
        action = "watch_seed"
    elif latest_gate and str(latest_gate.get("execution_gate") or "").lower() != "pass":
        action = "review_gate_block"
    elif freshness_status in {"blocked", "stale", "unavailable"}:
        action = "refresh_pipeline_inputs"
    elif latest_alert and str(latest_alert.get("severity") or "").lower() in {"red", "critical", "amber"}:
        action = "prioritize_review"
    elif latest_anomaly and _to_float(latest_anomaly.get("anomaly_score")) is not None and _to_float(latest_anomaly.get("anomaly_score")) >= high_anomaly_score:
        action = "prioritize_review"
    elif difficulty_score >= hard_difficulty_min:
        action = "review_hard_market"
    else:
        action = "open_workstation"

    return {
        "recommended_action": action,
        "action_mapping_policy_ref": policy_ref(policy, "action_mapping_policy.default"),
    }


def _to_float(value: object) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except Exception:
        return None
