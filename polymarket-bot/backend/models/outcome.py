from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from backend.models.core import now_iso


class MarketOutcomeSource(str, Enum):
    MANUAL = "MANUAL"
    WEATHER_ACTUAL = "WEATHER_ACTUAL"
    POLYMARKET = "POLYMARKET"
    UNKNOWN = "UNKNOWN"


class ResolvedOutcome(str, Enum):
    YES = "YES"
    NO = "NO"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNKNOWN = "UNKNOWN"


class ResolutionStatus(str, Enum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNKNOWN = "UNKNOWN"


class WeatherActualSource(str, Enum):
    MANUAL = "MANUAL"
    OPEN_METEO = "OPEN_METEO"
    NOAA_PLACEHOLDER = "NOAA_PLACEHOLDER"
    OBSERVATION = "OBSERVATION"
    UNKNOWN = "UNKNOWN"


class OutcomeMetric(str, Enum):
    TEMPERATURE_HIGH = "temperature_high"
    TEMPERATURE_LOW = "temperature_low"
    RAINFALL = "rainfall"
    SNOWFALL = "snowfall"
    WIND = "wind"
    UNKNOWN = "unknown"


class OutcomeUnit(str, Enum):
    C = "C"
    F = "F"
    MM = "MM"
    INCH = "INCH"
    MPS = "MPS"
    UNKNOWN = "UNKNOWN"


class OutcomeDirection(str, Enum):
    ABOVE = "ABOVE"
    BELOW = "BELOW"
    UNKNOWN = "UNKNOWN"


class MarketOutcomeRecord(BaseModel):
    market_outcome_id: str
    market_id: str
    question: str | None = None
    source: MarketOutcomeSource = MarketOutcomeSource.UNKNOWN
    resolved_outcome: ResolvedOutcome = ResolvedOutcome.UNKNOWN
    resolution_status: ResolutionStatus = ResolutionStatus.UNKNOWN
    resolved_value: float | None = None
    resolved_at: str = Field(default_factory=now_iso)
    notes: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WeatherActualRecord(BaseModel):
    weather_actual_id: str
    market_id: str
    city: str | None = None
    target_date: str | None = None
    source: WeatherActualSource = WeatherActualSource.UNKNOWN
    metric: OutcomeMetric = OutcomeMetric.UNKNOWN
    unit: OutcomeUnit = OutcomeUnit.UNKNOWN
    actual_value: float | None = None
    observed_at: str = Field(default_factory=now_iso)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OutcomeResolutionRecord(BaseModel):
    outcome_resolution_id: str
    market_id: str
    market_outcome_id: str | None = None
    weather_actual_id: str | None = None
    weather_view_id: str | None = None
    threshold: float | None = None
    direction: OutcomeDirection = OutcomeDirection.UNKNOWN
    actual_value: float | None = None
    resolved_outcome: ResolvedOutcome = ResolvedOutcome.UNKNOWN
    resolution_status: ResolutionStatus = ResolutionStatus.UNKNOWN
    resolution_source: MarketOutcomeSource = MarketOutcomeSource.UNKNOWN
    resolved_at: str = Field(default_factory=now_iso)
    notes: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OutcomeBundle(BaseModel):
    market_id: str
    markets: list[MarketOutcomeRecord] = Field(default_factory=list)
    weather_actuals: list[WeatherActualRecord] = Field(default_factory=list)
    resolutions: list[OutcomeResolutionRecord] = Field(default_factory=list)


class OutcomeArchiveSummary(BaseModel):
    market_outcome_records: int = 0
    weather_actual_records: int = 0
    outcome_resolution_records: int = 0
    unique_markets: int = 0
    by_resolution_status: dict[str, int] = Field(default_factory=dict)
    by_resolved_outcome: dict[str, int] = Field(default_factory=dict)
    latest_resolved_at: str | None = None
