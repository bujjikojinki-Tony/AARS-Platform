from __future__ import annotations

from backend.models.weather import WeatherView
from backend.probability.gaussian_probability_engine import GaussianProbabilityEngine


class DebShadowEngine:
    engine_id = "deb_shadow_v0"

    def __init__(self):
        self.gaussian = GaussianProbabilityEngine()

    def compute(self, weather_view: WeatherView) -> tuple[float, list[str]]:
        base_probability, warnings = self.gaussian.compute(weather_view)
        probability = base_probability * 0.95 + 0.025
        probability = self._clamp(probability)
        warnings = list(warnings)
        warnings.append(
            "deb_shadow_v0 is a placeholder shadow engine; it does not implement real DEB."
        )
        return probability, warnings

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))
