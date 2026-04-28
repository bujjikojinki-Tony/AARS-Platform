from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ForecastSnapshot(BaseModel):
    model_config = ConfigDict(extra="allow")

    location_name: str
    forecast_issued_at: datetime
    target_date: str
    variable_name: str
    value: float
    source: str
    source_mode: str | None = None
    source_path: str | None = None
    notes: str | None = None
    raw_value: float | None = None
    raw_unit: str | None = None
    canonical_value: float | None = None
    canonical_unit: str | None = None
    display_value: float | None = None
    display_unit: str | None = None
    conversion_rule: str | None = None
    conversion_applied: bool = False
    precision_policy_ref: str | None = None
    rounding_policy_ref: str | None = None
    band_mapping_policy_ref: str | None = None
    normalization_version: str = "measurement_normalization.v1"
