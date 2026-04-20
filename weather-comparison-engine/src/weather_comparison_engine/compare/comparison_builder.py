from __future__ import annotations

from weather_comparison_engine.compare.band_compare import BandCompare
from weather_comparison_engine.compare.confidence_compare import ConfidenceCompare
from weather_comparison_engine.compare.divergence_tracker import DivergenceTracker
from weather_comparison_engine.models.comparison_state import ComparisonState
from weather_comparison_engine.models.divergence_state import DivergenceState


class ComparisonBuilder:
    def __init__(self) -> None:
        self.band_compare = BandCompare()
        self.confidence_compare = ConfidenceCompare()
        self.divergence_tracker = DivergenceTracker()

    def build(self, signal: dict, market_bundle: dict) -> ComparisonState:
        market = market_bundle["market"]
        price_state = market_bundle["price_state"]

        model_band = signal.get("model_band")
        market_band = price_state.get("implied_band") or signal.get("market_band")
        confidence_score = float(signal.get("confidence", {}).get("score", 0.0))

        band_distance = self.band_compare.distance(model_band, market_band)
        adjusted_gap = self.confidence_compare.adjusted_gap(
            band_distance=band_distance,
            confidence_score=confidence_score,
        )
        status = self.divergence_tracker.classify(band_distance)

        divergence = DivergenceState(
            status=status,
            band_distance=band_distance,
            confidence_adjusted_gap=adjusted_gap,
        )

        return ComparisonState(
            market_id=signal["market_id"],
            market_question=market.get("market_question"),
            location_name=signal["location_name"],
            target_date=signal["target_date"],
            variable_name=signal["variable_name"],
            model_band=model_band,
            market_band=market_band,
            model_value=signal.get("model_value"),
            confidence_score=confidence_score,
            divergence=divergence,
            action_hint=signal["action_hint"],
        )
