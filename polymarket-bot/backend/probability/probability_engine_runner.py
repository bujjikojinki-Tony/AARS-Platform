from __future__ import annotations

from uuid import uuid4

from backend.models.probability_governance import ProbabilityEngineRun
from backend.models.probability_governance import ProbabilityEngineType
from backend.models.weather import WeatherView
from backend.probability.deb_shadow_engine import DebShadowEngine
from backend.probability.emos_shadow_engine import EmosShadowEngine
from backend.probability.gaussian_probability_engine import GaussianProbabilityEngine


class ProbabilityEngineRunner:
    def __init__(self, repository, registry):
        self.repository = repository
        self.registry = registry
        self.engines = {
            "gaussian_v0": GaussianProbabilityEngine(),
            "deb_shadow_v0": DebShadowEngine(),
            "emos_shadow_v0": EmosShadowEngine(),
        }

    def run_all(self, weather_view: WeatherView) -> list[ProbabilityEngineRun]:
        configs = self.registry.get_enabled_configs()
        runs: list[ProbabilityEngineRun] = []
        for config in configs:
            engine_id = config["engine_id"]
            engine = self.engines.get(engine_id)
            if not engine:
                continue
            probability, warnings = engine.compute(weather_view)
            run = ProbabilityEngineRun(
                run_id=f"per_{uuid4().hex[:10]}",
                market_id=weather_view.market_id,
                weather_view_id=weather_view.weather_view_id,
                engine_id=engine_id,
                engine_type=ProbabilityEngineType(config["engine_type"]),
                model_probability=probability,
                expected_value=weather_view.expected_value,
                sigma=weather_view.sigma,
                threshold=weather_view.threshold,
                direction=weather_view.direction.value,
                params=config.get("default_params", {}),
                warnings=warnings,
            )
            self.repository.save_probability_engine_run(run)
            runs.append(run)
        return runs
