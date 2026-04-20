from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from weather_comparison_engine.schemas.probability_contract import build_probability_contract


class ProbabilityState(BaseModel):
    """Shadow probability output; not a calibrated trading probability."""

    model_config = ConfigDict(extra="allow")

    schema_version: str = Field(default="probability_state.v1")
    market_id: str
    timestamp: str

    mode: str = "shadow"
    calibration_status: str = "not_calibrated"
    probability_mode: str = "heuristic_not_calibrated"
    execution_constraint: str = "manual_advisory_only"
    contract_version: str = "probability_contract.v1"
    probability_contract: dict = Field(default_factory=dict)
    model_id: str | None = None
    validation_ref: str | None = None
    method: str = "band_support_heuristic"
    approved_for_live: bool = False
    deployment_mode: str = "shadow"
    promotion_reason: str | None = None
    contract_source: str | None = None
    validation_report_generated_at: str | None = None

    market_implied_probability: float | None = None
    model_probability: float | None = None
    fair_value: float | None = None
    forecast_support_score: float | None = None
    confidence: float | None = None
    edge: float | None = None
    confidence_adjusted_edge: float | None = None

    resolver_status: str | None = None
    resolver_reason: str | None = None
    market_family: str | None = None
    required_data_source: str | None = None
    band_scheme: str | None = None

    market_band: str | None = None
    model_band: str | None = None
    expected_band: str | None = None
    probability_reason: str | None = None

    def model_post_init(self, __context: object) -> None:
        if not self.probability_contract:
            self.probability_contract = build_probability_contract(self.model_dump(mode="json", exclude_none=True))
