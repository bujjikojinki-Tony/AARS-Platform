from __future__ import annotations


def build_microstructure_stress(*, market_row: dict) -> dict:
    spread = _to_float(market_row.get("spread"))
    liquidity = _to_float(market_row.get("liquidity")) or _to_float(market_row.get("volume_24hr"))
    one_sided_pressure = _to_float(market_row.get("one_sided_pressure"))
    flip_frequency = _to_float(market_row.get("favored_side_flip_frequency"))

    spread_jump = min(1.0, max(spread, 0.0) * 5.0)
    liquidity_drop = 1.0 if liquidity <= 0 else max(0.0, min(1.0, 1.0 - min(liquidity / 100000.0, 1.0)))
    pressure = max(0.0, min(1.0, one_sided_pressure))
    flip = max(0.0, min(1.0, flip_frequency))
    score = min(1.0, (spread_jump * 0.35) + (liquidity_drop * 0.25) + (pressure * 0.25) + (flip * 0.15))

    return {
        "spread_jump": round(spread_jump, 4),
        "liquidity_drop": round(liquidity_drop, 4),
        "one_sided_pressure": round(pressure, 4),
        "favored_side_flip_frequency": round(flip, 4),
        "microstructure_stress_score": round(score, 4),
        "microstructure_stress_bucket": _bucket(score),
    }


def _bucket(score: float) -> str:
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
