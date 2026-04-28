from __future__ import annotations

from datetime import datetime

from weather_comparison_engine.monitoring_layer.observation_alert_layer.models import ObservationShockResult


def build_observation_shock_result(
    *,
    observation_snapshot: dict,
    previous_observation_snapshot: dict | None = None,
    threshold_policy: dict | None = None,
    source_match_grade: str | None = None,
) -> dict:
    current_value = _to_float(
        observation_snapshot.get("observation_canonical_value")
        or observation_snapshot.get("canonical_value")
    )
    previous_value = _to_float(
        (previous_observation_snapshot or {}).get("observation_canonical_value")
        or (previous_observation_snapshot or {}).get("canonical_value")
    )
    threshold_cross_value = _policy_value(threshold_policy, "threshold_cross_value")
    if threshold_cross_value is None:
        threshold_cross_value = _to_float(
            observation_snapshot.get("threshold_cross_value")
            or observation_snapshot.get("observation_band")
        )

    delta = None if current_value is None or previous_value is None else current_value - previous_value
    delta_abs = None if delta is None else abs(delta)
    direction = None
    if delta is not None:
        direction = "up" if delta > 0 else "down" if delta < 0 else None

    threshold_cross = False
    if current_value is not None and previous_value is not None and threshold_cross_value is not None:
        threshold_cross = (
            (previous_value < threshold_cross_value <= current_value)
            or (previous_value > threshold_cross_value >= current_value)
        )

    slope = None
    delta_minutes = _delta_minutes(
        (previous_observation_snapshot or {}).get("observed_at"),
        observation_snapshot.get("observed_at"),
    )
    if delta is not None and delta_minutes and delta_minutes > 0:
        slope = delta / delta_minutes

    review_only = str(source_match_grade or observation_snapshot.get("source_match_grade") or "").strip().lower() != "exact_station"
    return {
        "threshold_cross_value": threshold_cross_value,
        "threshold_cross_event": threshold_cross,
        "threshold_cross_direction": direction if threshold_cross else None,
        "shock_delta_value": delta,
        "shock_delta_abs": delta_abs,
        "shock_slope_per_minute": slope,
        "review_only": review_only,
        "input_mode": "canonical_only",
    }


def _policy_value(policy: dict | None, key: str, default: float | None = None) -> float | None:
    policy = policy or {}
    threshold_value = policy.get("threshold_value") or {}
    try:
        return float(threshold_value.get(key, default))
    except (TypeError, ValueError):
        return default


def _delta_minutes(previous_at: str | None, current_at: str | None) -> float | None:
    if not previous_at or not current_at:
        return None
    try:
        prev = datetime.fromisoformat(str(previous_at).replace("Z", "+00:00"))
        curr = datetime.fromisoformat(str(current_at).replace("Z", "+00:00"))
    except ValueError:
        return None
    return (curr - prev).total_seconds() / 60.0


def _to_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
