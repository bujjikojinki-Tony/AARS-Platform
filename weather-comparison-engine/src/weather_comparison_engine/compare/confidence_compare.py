from __future__ import annotations


class ConfidenceCompare:
    def adjusted_gap(self, band_distance: int, confidence_score: float) -> float:
        if band_distance >= 999:
            return 0.0
        return band_distance * confidence_score


def compare_confidence_level(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"
