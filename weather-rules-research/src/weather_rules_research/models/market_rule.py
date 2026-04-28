from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from weather_rules_research.governance import build_policy_refs
from weather_rules_research.registries.band_scheme_registry import resolve_band_scheme


def _market_family_for_variable(variable_name: str) -> str:
    if variable_name in {"daily_max_temperature", "daily_min_temperature"}:
        return "station_temperature"
    if variable_name in {
        "daily_precipitation_sum",
        "daily_snowfall_sum",
        "daily_max_wind_speed",
    }:
        return "weather_metric"
    return "unknown"


class MarketRule(BaseModel):
    market_id: str
    market_question: str
    market_type: str = Field(description="e.g. daily_high_temperature")
    location_name: str
    target_date: str | None = None
    station_name: str | None = None
    nws_station_id: str | None = None
    cdo_station_id: str | None = None
    variable_name: str = Field(description="e.g. daily_max_temperature")
    timezone: str
    source_name: str
    raw_rules_text: str
    parse_confidence: float = 0.0
    needs_review: bool = True
    source_policy_ref: str | None = None
    unit_policy_ref: str | None = None
    precision_policy_ref: str | None = None
    rounding_policy_ref: str | None = None
    band_mapping_policy_ref: str | None = None

    @model_validator(mode="after")
    def _populate_policy_refs(self) -> "MarketRule":
        band_scheme = resolve_band_scheme(
            variable_name=self.variable_name,
            market_family=_market_family_for_variable(self.variable_name),
        )
        refs = build_policy_refs(
            market_family=_market_family_for_variable(self.variable_name),
            variable_name=self.variable_name,
            band_scheme=band_scheme,
        )
        for field_name, value in refs.items():
            if getattr(self, field_name) is None and value is not None:
                setattr(self, field_name, value)
        return self
