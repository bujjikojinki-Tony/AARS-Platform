from __future__ import annotations

from backend.models.probability_governance import ProbabilityEngineType


class ActiveEnginePolicy:
    """
    PWB-03 active engine policy.
    Rules:
    - Only enabled PRIMARY engines can be active.
    - can_be_primary must be true.
    - SHADOW engines cannot be active.
    - DISABLED engines cannot be active.
    """

    def validate_active_engine(self, config: dict) -> tuple[bool, str]:
        if not config:
            return False, "engine config not found"
        if config.get("enabled") is not True:
            return False, "engine is disabled"
        if config.get("engine_type") != ProbabilityEngineType.PRIMARY.value:
            return False, "engine is not PRIMARY"
        if config.get("can_be_primary") is not True:
            return False, "engine cannot be primary"
        return True, "engine accepted as active"

    def select_active_engine(self, configs: list[dict]) -> dict:
        for config in configs:
            ok, _ = self.validate_active_engine(config)
            if ok:
                return config
        raise ValueError("no valid active probability engine found")
