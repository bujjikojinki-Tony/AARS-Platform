from __future__ import annotations

from weather_signal_engine.features.model_vs_market_edge import estimate_model_vs_market_edge
from weather_signal_engine.features.temperature_band import classify_temperature_band
class EdgeEstimator:
    def estimate(
        self,
        model_value: float,
        market_band: str | None,
    ) -> tuple[str | None, float, str]:
        model_band = classify_temperature_band(model_value)
        return estimate_model_vs_market_edge(
            model_band=model_band,
            market_band=market_band,
        ) + (model_band,)
