from __future__ import annotations

from weather_comparison_engine.monitoring_layer.observation_alert_layer.models import ForecastDivergenceResult


def build_forecast_divergence_result(
    *,
    observation_snapshot: dict,
    forecast_snapshot: dict,
    market_rule: dict | None = None,
    source_confidence: float | None = None,
) -> dict:
    observation_value = _to_float(
        observation_snapshot.get("observation_canonical_value")
        or observation_snapshot.get("canonical_value")
    )
    forecast_value = _to_float(
        forecast_snapshot.get("forecast_canonical_value")
        or forecast_snapshot.get("canonical_value")
    )

    value_divergence = None if observation_value is None or forecast_value is None else observation_value - forecast_value
    value_divergence_abs = None if value_divergence is None else abs(value_divergence)
    band_divergence = _string_value(observation_snapshot.get("observation_band") or observation_snapshot.get("official_band")) != _string_value(
        forecast_snapshot.get("model_band") or forecast_snapshot.get("band")
    )

    band_distance = 0 if not band_divergence else 1
    confidence = _to_float(source_confidence if source_confidence is not None else forecast_snapshot.get("source_confidence")) or 1.0
    forecast_divergence_score = None if value_divergence_abs is None else value_divergence_abs * confidence

    invalid_comparison, comparison_block_reason = _comparison_guard(observation_snapshot, forecast_snapshot, market_rule)

    return {
        "value_divergence": value_divergence,
        "value_divergence_abs": value_divergence_abs,
        "band_divergence": band_divergence,
        "band_distance": band_distance,
        "forecast_divergence_score": forecast_divergence_score,
        "invalid_comparison": invalid_comparison,
        "comparison_block_reason": comparison_block_reason,
        "input_mode": "canonical_only",
    }


def _comparison_guard(observation_snapshot: dict, forecast_snapshot: dict, market_rule: dict | None) -> tuple[bool, str | None]:
    market_id_a = _string_value(observation_snapshot.get("market_id") or forecast_snapshot.get("market_id"))
    market_id_b = _string_value((market_rule or {}).get("market_id") or forecast_snapshot.get("rule_market_id"))
    variable_a = _string_value(observation_snapshot.get("variable_name") or forecast_snapshot.get("variable_name"))
    variable_b = _string_value((market_rule or {}).get("variable_name"))
    target_date_a = _string_value(observation_snapshot.get("target_date") or forecast_snapshot.get("target_date"))
    target_date_b = _string_value((market_rule or {}).get("target_date"))
    station_a = _string_value(observation_snapshot.get("station_id") or forecast_snapshot.get("station_id"))
    station_b = _string_value((market_rule or {}).get("station_id"))

    mismatches: list[str] = []
    if market_id_a and market_id_b and market_id_a != market_id_b:
        mismatches.append("market_id")
    if variable_a and variable_b and variable_a != variable_b:
        mismatches.append("variable_name")
    if target_date_a and target_date_b and target_date_a != target_date_b:
        mismatches.append("target_date")
    if station_a and station_b and station_a != station_b:
        mismatches.append("station_id")

    if mismatches:
        return True, f"comparison_blocked:{','.join(mismatches)}"
    return False, None


def _string_value(value: object) -> str:
    return str(value).strip() if value not in (None, "") else ""


def _to_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
