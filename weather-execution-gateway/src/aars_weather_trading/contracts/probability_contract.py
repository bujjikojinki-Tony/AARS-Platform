from dataclasses import dataclass

from aars_weather_trading.contracts.contract_versions import PROBABILITY_CONTRACT_VERSION


@dataclass(frozen=True)
class ProbabilityContract:
    probability_mode: str
    calibration_status: str
    execution_constraint: str
    model_id: str | None = None
    validation_ref: str | None = None
    contract_version: str = PROBABILITY_CONTRACT_VERSION

