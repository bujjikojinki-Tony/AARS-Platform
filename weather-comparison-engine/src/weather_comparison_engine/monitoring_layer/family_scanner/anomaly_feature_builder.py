from __future__ import annotations


def build_anomaly_features(*, market_row: dict, comparison_history: list[dict], probability_state: dict | None = None) -> dict:
    probability_state = probability_state or {}
    market_id = str(market_row.get("market_id") or "")
    family = str(market_row.get("market_family") or "-")
    peer_rows = [row for row in comparison_history if str(row.get("market_family") or "") == family]
    market_prob = _pick_float(
        market_row,
        "market_probability",
        "display_market_probability",
        "model_probability",
    )
    fair_value = _pick_float(
        probability_state,
        "fair_value_canonical",
        "canonical_value",
        "fair_value",
    )
    if fair_value is None:
        fair_value = _pick_float(market_row, "model_canonical_value", "model_value", "fair_value")
    edge_dislocation = abs((fair_value or 0.0) - (market_prob or 0.0)) if fair_value is not None and market_prob is not None else None
    price_velocity = _price_velocity(market_id, comparison_history, market_prob)
    evidence_mismatch = _evidence_mismatch(market_row, comparison_history)
    microstructure_stress = _microstructure_stress(market_row)
    peer_relative_anomaly = _peer_relative_anomaly(market_row, peer_rows, edge_dislocation)
    intervention_like_score = _intervention_like_score(
        price_velocity=price_velocity,
        edge_dislocation=edge_dislocation,
        evidence_mismatch=evidence_mismatch,
        microstructure_stress=microstructure_stress,
        peer_relative_anomaly=peer_relative_anomaly,
    )
    feature_breakdown = {
        "price_velocity": round(price_velocity, 4),
        "edge_dislocation": round(edge_dislocation, 4) if edge_dislocation is not None else None,
        "evidence_mismatch_score": round(evidence_mismatch["evidence_mismatch_score"], 4),
        "microstructure_stress_score": round(microstructure_stress, 4),
        "peer_rank": peer_relative_anomaly["peer_rank"],
        "peer_zscore": peer_relative_anomaly["peer_zscore"],
        "peer_outlier_flag": peer_relative_anomaly["peer_outlier_flag"],
    }

    return {
        "market_id": market_id,
        "market_family": family,
        "price_velocity": price_velocity,
        "edge_dislocation": edge_dislocation,
        "evidence_mismatch": evidence_mismatch["evidence_mismatch"],
        "evidence_mismatch_score": evidence_mismatch["evidence_mismatch_score"],
        "microstructure_stress_score": microstructure_stress,
        "peer_rank": peer_relative_anomaly["peer_rank"],
        "peer_zscore": peer_relative_anomaly["peer_zscore"],
        "peer_outlier_flag": peer_relative_anomaly["peer_outlier_flag"],
        "intervention_like_score": intervention_like_score,
        "intervention_like_flag": intervention_like_score >= 0.8,
        "anomaly_bucket": _anomaly_bucket(intervention_like_score),
        "input_mode": "canonical_only",
        "market_probability": market_prob,
        "fair_value": fair_value,
        "feature_breakdown": feature_breakdown,
    }


def _price_velocity(market_id: str, comparison_history: list[dict], current_probability: float | None) -> float:
    if current_probability is None:
        return 0.0
    previous = None
    for row in reversed(comparison_history):
        if str(row.get("market_id") or "") == market_id:
            previous = _to_float(row.get("market_probability"))
            break
    if previous is None:
        return 0.0
    return abs(current_probability - previous)


def _evidence_mismatch(market_row: dict, comparison_history: list[dict]) -> dict:
    current_move = _pick_float(
        market_row,
        "confidence_adjusted_gap",
        "canonical_confidence_adjusted_gap",
        "band_distance",
        default=0.0,
    ) or 0.0
    previous_move = 0.0
    for row in reversed(comparison_history):
        if str(row.get("market_id") or "") == str(market_row.get("market_id") or ""):
            previous_move = _pick_float(
                row,
                "confidence_adjusted_gap",
                "canonical_confidence_adjusted_gap",
                "band_distance",
                default=0.0,
            ) or 0.0
            break
    mismatch = (current_move > 0 and previous_move < 0) or (current_move < 0 and previous_move > 0)
    return {
        "evidence_mismatch": mismatch,
        "evidence_mismatch_score": abs(current_move - previous_move),
    }


def _microstructure_stress(market_row: dict) -> float:
    spread = _to_float(market_row.get("spread")) or 0.0
    liquidity = _to_float(market_row.get("liquidity")) or _to_float(market_row.get("volume_24hr")) or 0.0
    side_bias = 1.0 if str(market_row.get("favored_side") or "").lower() in {"yes", "no"} else 0.5
    stress = min(1.0, (spread * 5.0) + (0.2 if liquidity <= 0 else 0.0) + (0.2 * side_bias))
    return round(stress, 4)


def _peer_relative_anomaly(market_row: dict, peer_rows: list[dict], edge_dislocation: float | None) -> dict:
    if not peer_rows:
        return {"peer_rank": 0, "peer_zscore": 0.0, "peer_outlier_flag": False}
    sorted_peers = sorted(
        (_pick_float(row, "confidence_adjusted_gap", "canonical_confidence_adjusted_gap", "band_distance", default=0.0) or 0.0 for row in peer_rows),
    )
    rank = 1 + sum(1 for value in sorted_peers if value < (edge_dislocation or 0.0))
    mean = sum(sorted_peers) / len(sorted_peers)
    variance = sum((value - mean) ** 2 for value in sorted_peers) / len(sorted_peers)
    std = variance ** 0.5 if variance > 0 else 0.0
    zscore = 0.0 if std == 0 else ((edge_dislocation or 0.0) - mean) / std
    return {
        "peer_rank": rank,
        "peer_zscore": round(zscore, 4),
        "peer_outlier_flag": abs(zscore) >= 2.0,
    }


def _intervention_like_score(
    *,
    price_velocity: float,
    edge_dislocation: float | None,
    evidence_mismatch: dict,
    microstructure_stress: float,
    peer_relative_anomaly: dict,
) -> float:
    edge = edge_dislocation or 0.0
    score = (
        min(1.0, price_velocity * 5.0) * 0.25
        + min(1.0, edge * 5.0) * 0.25
        + min(1.0, evidence_mismatch.get("evidence_mismatch_score", 0.0)) * 0.2
        + microstructure_stress * 0.2
        + min(1.0, abs(peer_relative_anomaly.get("peer_zscore", 0.0)) / 3.0) * 0.1
    )
    return round(min(1.0, score), 4)


def _anomaly_bucket(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def _to_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _pick_float(source: dict, *keys: str, default: float | None = None) -> float | None:
    for key in keys:
        if key in source and source.get(key) not in (None, ""):
            value = _to_float(source.get(key))
            if value is not None:
                return value
    return default
