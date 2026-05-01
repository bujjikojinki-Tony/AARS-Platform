from __future__ import annotations

from backend.models.probability_governance import ProbabilityEngineType


class ProbabilityEngineRegistry:
    def __init__(self, repository):
        self.repository = repository

    def list_configs(self) -> list[dict]:
        return self.repository.list_probability_engine_configs()

    def get_enabled_configs(self) -> list[dict]:
        return [cfg for cfg in self.list_configs() if cfg.get("enabled") is True]

    def get_primary_engine_config(self) -> dict | None:
        for cfg in self.get_enabled_configs():
            if cfg.get("engine_type") == ProbabilityEngineType.PRIMARY.value:
                return cfg
        return None

    def get_shadow_engine_configs(self) -> list[dict]:
        return [
            cfg
            for cfg in self.get_enabled_configs()
            if cfg.get("engine_type") == ProbabilityEngineType.SHADOW.value
        ]

    def get_config(self, engine_id: str) -> dict | None:
        return self.repository.get_probability_engine_config(engine_id)
