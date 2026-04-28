from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from .station import Station


class ForecastSnapshot(BaseModel):
    model_config = ConfigDict(extra="allow")

    market_id: str
    station_id: str
    market_type: str
    target_date: date
    issued_at: str = Field(description="ISO-8601 timestamp when the forecast was issued.")
    predicted_temperature_c: float
    source: str = "open-meteo"
    raw_payload_ref: str | None = None
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


class StationMapEntry(BaseModel):
    market_id: str
    station: Station


class JoinedRecord(BaseModel):
    market_id: str
    station_id: str
    market_type: str
    settlement_date: date
    predicted_temperature_c: float
    settled_temperature_c: float
    forecast_issued_at: str
    forecast_source: str
    settlement_source: str
    settlement_unit: str
    settlement_source_url: str | None = None
    settlement_raw_payload_ref: str | None = None

    @property
    def forecast_value(self) -> float:
        return self.predicted_temperature_c

    @property
    def official_value(self) -> float:
        return self.settled_temperature_c

    @property
    def error(self) -> float:
        return self.forecast_value - self.official_value


class BiasReportRow(BaseModel):
    market_id: str
    station_id: str
    market_type: str
    settlement_date: date
    predicted_temperature_c: float
    settled_temperature_c: float
    error_c: float
    abs_error_c: float
    squared_error_c: float
    forecast_source: str
    band_hit: bool


class BiasSummary(BaseModel):
    sample_size: int
    mean_error_c: float
    mae_c: float
    rmse_c: float
    band_c: float
    band_hit_rate: float
