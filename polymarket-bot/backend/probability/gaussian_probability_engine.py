import math

from backend.models.weather import WeatherDirection
from backend.models.weather import WeatherView


class GaussianProbabilityEngine:
    engine_id = "gaussian_v0"

    def compute(self, weather_view: WeatherView) -> tuple[float, list[str]]:
        warnings: list[str] = []
        if weather_view.threshold is None:
            warnings.append("threshold is missing")
            return 0.5, warnings
        if weather_view.sigma <= 0:
            warnings.append("sigma must be positive")
            return 0.5, warnings

        z = (weather_view.threshold - weather_view.expected_value) / weather_view.sigma
        cdf_value = self._normal_cdf(z)
        if weather_view.direction == WeatherDirection.ABOVE:
            probability = 1 - cdf_value
        elif weather_view.direction == WeatherDirection.BELOW:
            probability = cdf_value
        elif weather_view.direction == WeatherDirection.BETWEEN:
            warnings.append("BETWEEN direction requires upper_threshold; fallback to 0.5")
            probability = 0.5
        else:
            warnings.append("unknown direction; fallback to 0.5")
            probability = 0.5
        return self._clamp(probability), warnings

    def _normal_cdf(self, z: float) -> float:
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))
