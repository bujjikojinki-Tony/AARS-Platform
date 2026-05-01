from __future__ import annotations

from backend.models.weather import WeatherView
from backend.probability.gaussian_probability_engine import GaussianProbabilityEngine


class EmosShadowEngine:
    engine_id = "emos_shadow_v0"

    def __init__(self):
        self.gaussian = GaussianProbabilityEngine()

    def compute(self, weather_view: WeatherView) -> tuple[float, list[str]]:
        base_probability, warnings = self.gaussian.compute(weather_view)
        probability = 0.5 + (base_probability - 0.5) * 0.85
        probability = self._clamp(probability)
        warnings = list(warnings)
        warnings.append(
            "emos_shadow_v0 is a placeholder shadow engine; it does not implement real EMOS."
        )
        return probability, warnings

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))
