from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ObservationAlertInput:
    market_snapshot: dict
    forecast_snapshot: dict
    observation_snapshot: dict
    previous_observation_snapshot: dict | None = None
    comparison_point: dict | None = None
    threshold_policy: dict | None = None


@dataclass(slots=True)
class ObservationShockResult:
    threshold_cross_value: float | None = None
    threshold_cross_event: bool = False
    threshold_cross_direction: str | None = None
    shock_delta_value: float | None = None
    shock_delta_abs: float | None = None
    shock_slope_per_minute: float | None = None
    review_only: bool = False


@dataclass(slots=True)
class ForecastDivergenceResult:
    value_divergence: float | None = None
    value_divergence_abs: float | None = None
    band_divergence: bool | None = None
    band_distance: int | None = None
    forecast_divergence_score: float | None = None
    invalid_comparison: bool = False
    comparison_block_reason: str | None = None


@dataclass(slots=True)
class MarketReactionGapResult:
    fair_value_gap: float | None = None
    reaction_lag_score: float | None = None
    market_band_mismatch: bool | None = None


@dataclass(slots=True)
class SourceRiskResult:
    source_match_risk: str = "unknown"
    officialness_risk: str = "unknown"
    freshness_risk: str = "unknown"


@dataclass(slots=True)
class MarketAlertEvent:
    schema_version: str
    market_id: str
    event_type: str
    severity: str
    primary_reason: str
    recommended_operator_action: str
    observation_value: float | None
    forecast_value: float | None
    market_probability: float | None
    fair_value: float | None
    source_match_grade: str
    freshness_status: str
    generated_at: str
    contract_version: str = "v1"
