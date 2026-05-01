from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from backend.models.core import now_iso


class WeatherArchiveReason(str, Enum):
    WEATHER_VIEW_CAPTURE = "WEATHER_VIEW_CAPTURE"
    PROBABILITY_BUILD_CAPTURE = "PROBABILITY_BUILD_CAPTURE"
    MANUAL_CAPTURE = "MANUAL_CAPTURE"
    SCAN_CAPTURE = "SCAN_CAPTURE"


class WeatherForecastSourceType(str, Enum):
    MOCK = "MOCK"
    OPEN_METEO = "OPEN_METEO"
    NOAA_PLACEHOLDER = "NOAA_PLACEHOLDER"
    UNKNOWN = "UNKNOWN"


class WeatherArchiveMetric(str, Enum):
    TEMPERATURE_HIGH = "temperature_high"
    TEMPERATURE_LOW = "temperature_low"
    RAINFALL = "rainfall"
    SNOWFALL = "snowfall"
    WIND = "wind"
    UNKNOWN = "unknown"


class WeatherArchiveUnit(str, Enum):
    C = "C"
    F = "F"
    MM = "MM"
    INCH = "INCH"
    MPS = "MPS"
    UNKNOWN = "UNKNOWN"


class WeatherForecastArchiveRecord(BaseModel):
    forecast_archive_id: str
    market_id: str
    weather_view_id: str | None = None
    evidence_pack_id: str | None = None
    city: str | None = None
    target_date: str | None = None
    source_id: str
    source_type: WeatherForecastSourceType = WeatherForecastSourceType.UNKNOWN
    metric: WeatherArchiveMetric = WeatherArchiveMetric.UNKNOWN
    unit: WeatherArchiveUnit = WeatherArchiveUnit.UNKNOWN
    expected_value: float | None = None
    expected_range_low: float | None = None
    expected_range_high: float | None = None
    sigma: float | None = None
    fetched_at: str | None = None
    archived_at: str = Field(default_factory=now_iso)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    archive_reason: WeatherArchiveReason


class WeatherEvidenceArchiveRecord(BaseModel):
    evidence_archive_id: str
    market_id: str
    evidence_pack_id: str
    source_ids: list[str] = Field(default_factory=list)
    evidence_summary: list[str] = Field(default_factory=list)
    invalidation_rules: list[str] = Field(default_factory=list)
    confirmation_rules: list[str] = Field(default_factory=list)
    archived_at: str = Field(default_factory=now_iso)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    archive_reason: WeatherArchiveReason


class WeatherViewArchiveRecord(BaseModel):
    weather_view_archive_id: str
    market_id: str
    weather_view_id: str
    evidence_pack_id: str | None = None
    city: str | None = None
    target_date: str | None = None
    expected_value: float | None = None
    expected_range_low: float | None = None
    expected_range_high: float | None = None
    sigma: float | None = None
    threshold: float | None = None
    direction: str = "UNKNOWN"
    unit: str = "UNKNOWN"
    confidence: str = "UNKNOWN"
    archived_at: str = Field(default_factory=now_iso)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    archive_reason: WeatherArchiveReason


class WeatherArchiveSummary(BaseModel):
    forecast_records: int = 0
    evidence_records: int = 0
    weather_view_records: int = 0
    unique_markets: int = 0
    by_source_type: dict[str, int] = Field(default_factory=dict)
    by_archive_reason: dict[str, int] = Field(default_factory=dict)
    latest_archived_at: str | None = None


class WeatherArchiveBundle(BaseModel):
    market_id: str
    forecasts: list[WeatherForecastArchiveRecord] = Field(default_factory=list)
    evidence: list[WeatherEvidenceArchiveRecord] = Field(default_factory=list)
    weather_views: list[WeatherViewArchiveRecord] = Field(default_factory=list)
