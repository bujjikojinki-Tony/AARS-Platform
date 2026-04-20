from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ForecastSnapshot(BaseModel):
    """Normalized read model for the current forecast / resolver snapshot."""

    model_config = ConfigDict(extra="allow")

    schema_version: str = Field(default="forecast_snapshot.v1")
    timestamp: str | None = None
    market_id: str

    location_name: str | None = None
    target_date: str | None = None
    variable_name: str | None = None

    value: float | int | None = None
    model_band: str | None = None
    confidence_score: float | None = None
    source_mode: str | None = None

    rule_status: str | None = None
    rule_market_id: str | None = None
    market_family: str | None = None
    resolution_scope: str | None = None
    supported_by_current_pipeline: bool | None = None
    required_data_source: str | None = None
    band_scheme: str | None = None

