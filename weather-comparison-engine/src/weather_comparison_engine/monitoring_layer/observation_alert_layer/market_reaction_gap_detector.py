from __future__ import annotations


def build_market_reaction_gap_result(
    *,
    market_snapshot: dict,
    probability_state: dict | None = None,
    comparison_point: dict | None = None,
    previous_market_snapshot: dict | None = None,
) -> dict:
    probability_state = probability_state or {}
    comparison_point = comparison_point or {}
    market_probability = _to_float(
        market_snapshot.get("market_probability")
        or comparison_point.get("market_probability")
        or probability_state.get("market_implied_probability")
    )
    fair_value = _to_float(
        probability_state.get("fair_value")
        or comparison_point.get("fair_value")
    )
    fair_value_gap = None if fair_value is None or market_probability is None else fair_value - market_probability

    prev_market_probability = _to_float((previous_market_snapshot or {}).get("market_probability"))
    evidence_change_score = abs(_to_float(comparison_point.get("confidence_adjusted_gap")) or 0.0)
    market_move_score = 0.0
    if prev_market_probability is not None and market_probability is not None:
        market_move_score = abs(market_probability - prev_market_probability)
    reaction_lag_score = evidence_change_score - market_move_score

    market_band_mismatch = _string_value(market_snapshot.get("market_band")) != _string_value(comparison_point.get("model_band"))

    return {
        "fair_value_gap": fair_value_gap,
        "reaction_lag_score": reaction_lag_score,
        "market_band_mismatch": market_band_mismatch,
        "input_mode": "canonical_only",
    }


def _string_value(value: object) -> str:
    return str(value).strip() if value not in (None, "") else ""


def _to_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
