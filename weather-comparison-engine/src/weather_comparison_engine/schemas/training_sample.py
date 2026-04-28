from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TrainingSample(BaseModel):
    """Point-in-time feature row for later backtest and calibration work."""

    model_config = ConfigDict(extra="allow")

    schema_version: str = Field(default="training_sample.v2")
    market_id: str
    timestamp: str

    market_question: str | None = None
    market_family: str | None = None
    band_scheme: str | None = None
    target_date: str | None = None
    variable_name: str | None = None
    station_id: str | None = None
    source_match_grade: str | None = None
    official_vs_proxy_source: str | None = None
    freshness_status: str | None = None
    source_policy_ref: str | None = None
    unit_policy_ref: str | None = None
    precision_policy_ref: str | None = None
    rounding_policy_ref: str | None = None
    band_mapping_policy_ref: str | None = None
    normalization_version: str | None = None

    raw_value: float | int | None = None
    raw_unit: str | None = None
    canonical_value: float | int | None = None
    canonical_unit: str | None = None
    display_value: float | int | None = None
    display_unit: str | None = None
    conversion_rule: str | None = None
    conversion_applied: bool | None = None

    market_probability: float | None = None
    yes_price: float | None = None
    no_price: float | None = None
    price_sum: float | None = None
    price_dislocation: float | None = None

    model_value: float | None = None
    model_raw_value: float | int | None = None
    model_canonical_value: float | int | None = None
    model_display_value: float | int | None = None
    model_raw_unit: str | None = None
    model_canonical_unit: str | None = None
    model_display_unit: str | None = None
    model_band: str | None = None
    market_band: str | None = None
    expected_band: str | None = None
    confidence_score: float | None = None
    confidence_adjusted_gap: float | None = None
    comparison_status: str | None = None
    action_hint: str | None = None

    forecast_raw_value: float | int | None = None
    forecast_canonical_value: float | int | None = None
    forecast_display_value: float | int | None = None
    forecast_raw_unit: str | None = None
    forecast_canonical_unit: str | None = None
    forecast_display_unit: str | None = None
    forecast_conversion_rule: str | None = None
    forecast_conversion_applied: bool | None = None
    forecast_normalization_version: str | None = None

    observation_raw_value: float | int | None = None
    observation_canonical_value: float | int | None = None
    observation_display_value: float | int | None = None
    observation_raw_unit: str | None = None
    observation_canonical_unit: str | None = None
    observation_display_unit: str | None = None
    observation_conversion_rule: str | None = None
    observation_conversion_applied: bool | None = None
    observation_normalization_version: str | None = None

    fair_value: float | None = None
    edge: float | None = None
    confidence_adjusted_edge: float | None = None
    probability_reason: str | None = None

    official_value: float | None = None
    resolved_band: str | None = None
    outcome: str | None = None
    is_labeled: bool = False
    label_source: str | None = None

    resolver_status: str | None = None
    resolver_reason: str | None = None
    required_data_source: str | None = None
    market_snapshot_ref: str | None = None
    forecast_snapshot_ref: str | None = None
