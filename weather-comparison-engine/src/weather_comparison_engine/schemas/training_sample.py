from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TrainingSample(BaseModel):
    """Point-in-time feature row for later backtest and calibration work."""

    model_config = ConfigDict(extra="allow")

    schema_version: str = Field(default="training_sample.v1")
    market_id: str
    timestamp: str

    market_question: str | None = None
    market_family: str | None = None
    band_scheme: str | None = None
    target_date: str | None = None
    variable_name: str | None = None
    station_id: str | None = None

    market_probability: float | None = None
    yes_price: float | None = None
    no_price: float | None = None
    price_sum: float | None = None
    price_dislocation: float | None = None

    model_value: float | None = None
    model_band: str | None = None
    market_band: str | None = None
    expected_band: str | None = None
    confidence_score: float | None = None
    confidence_adjusted_gap: float | None = None
    comparison_status: str | None = None
    action_hint: str | None = None

    model_probability: float | None = None
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
