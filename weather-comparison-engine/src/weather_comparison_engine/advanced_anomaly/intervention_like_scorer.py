from __future__ import annotations


def score_intervention_like(
    *,
    price_velocity_score: float,
    microstructure_stress_score: float,
    evidence_mismatch_score: float,
    peer_relative_anomaly_score: float,
    evidence_support_quality: float = 1.0,
) -> dict:
    score = (
        min(1.0, max(price_velocity_score, 0.0)) * 0.25
        + min(1.0, max(microstructure_stress_score, 0.0)) * 0.25
        + min(1.0, max(evidence_mismatch_score, 0.0)) * 0.2
        + min(1.0, max(peer_relative_anomaly_score, 0.0)) * 0.2
        + min(1.0, max(1.0 - evidence_support_quality, 0.0)) * 0.1
    )
    score = min(1.0, score)
    return {
        "intervention_like_score": round(score, 4),
        "intervention_like_flag": score >= 0.8,
    }
