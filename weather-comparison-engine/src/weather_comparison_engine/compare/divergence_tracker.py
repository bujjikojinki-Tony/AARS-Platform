from __future__ import annotations

from weather_comparison_engine.compare.band_compare import BandCompare


class DivergenceTracker:
    def classify(self, band_distance: int) -> str:
        if band_distance >= 999:
            return "unknown"
        if band_distance == 0:
            return "aligned"
        if band_distance == 1:
            return "mild_divergence"
        return "strong_divergence"


def compute_divergence_score(model_band: str | None, market_band: str | None) -> float:
    distance = BandCompare().distance(model_band, market_band)
    if distance >= 999:
        return 0.0
    if distance == 0:
        return 0.0
    return 1.0
