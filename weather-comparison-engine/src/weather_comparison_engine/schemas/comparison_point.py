from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ComparisonPoint(BaseModel):
    """Normalized read model for comparison history points."""

    model_config = ConfigDict(extra="allow")

    schema_version: str = Field(default="comparison_point.v1")
    timestamp: str
    market_id: str

    model_value: float | int | None = None
    model_band: str | None = None
    market_band: str | None = None

    market_probability: float | None = None
    fair_value: float | None = None
    edge: float | None = None

    band_distance: int | None = None
    confidence_score: float | None = None
    confidence_adjusted_gap: float | None = None
    comparison_status: str | None = None
    action_hint: str | None = None

    market_snapshot_ref: str | None = None
    forecast_snapshot_ref: str | None = None

