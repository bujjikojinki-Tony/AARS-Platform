from uuid import uuid4

from backend.models.weather import ProbabilityView
from backend.models.weather import WeatherView
from backend.probability.gaussian_probability_engine import GaussianProbabilityEngine


class ProbabilityViewBuilder:
    def __init__(self, engine: GaussianProbabilityEngine | None = None):
        self.engine = engine or GaussianProbabilityEngine()

    def build(self, weather_view: WeatherView) -> ProbabilityView:
        probability, warnings = self.engine.compute(weather_view)
        return ProbabilityView(
            probability_view_id=f"pv_{uuid4().hex[:10]}",
            weather_view_id=weather_view.weather_view_id,
            market_id=weather_view.market_id,
            engine_id=self.engine.engine_id,
            model_probability=probability,
            threshold=weather_view.threshold,
            expected_value=weather_view.expected_value,
            sigma=weather_view.sigma,
            direction=weather_view.direction,
            confidence=weather_view.confidence,
            warnings=warnings,
        )
