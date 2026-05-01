from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from backend.models.core import now_iso


class WeatherMetric(str, Enum):
    DAILY_HIGH = "DAILY_HIGH"
    DAILY_LOW = "DAILY_LOW"
    PRECIPITATION = "PRECIPITATION"
    UNKNOWN = "UNKNOWN"


class WeatherUnit(str, Enum):
    C = "C"
    F = "F"
    MM = "MM"
    IN = "IN"
    UNKNOWN = "UNKNOWN"


class WeatherDirection(str, Enum):
    ABOVE = "ABOVE"
    BELOW = "BELOW"
    BETWEEN = "BETWEEN"
    UNKNOWN = "UNKNOWN"


class ParseConfidence(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SourceType(str, Enum):
    FORECAST = "FORECAST"
    OBSERVATION = "OBSERVATION"
    SETTLEMENT = "SETTLEMENT"
    SHADOW = "SHADOW"


class FreshnessStatus(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    MISSING = "MISSING"


class TrustLevel(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    SHADOW = "SHADOW"


class EvidenceFreshness(str, Enum):
    FRESH = "FRESH"
    PARTIAL = "PARTIAL"
    STALE = "STALE"
    MISSING = "MISSING"


class EvidenceConflictLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class WeatherMarketDescriptor(BaseModel):
    market_id: str
    question: str
    city: str = "UNKNOWN"
    region: str | None = None
    country: str | None = None
    target_date: str = "UNKNOWN"
    metric: WeatherMetric = WeatherMetric.UNKNOWN
    threshold: float | None = None
    upper_threshold: float | None = None
    unit: WeatherUnit = WeatherUnit.UNKNOWN
    direction: WeatherDirection = WeatherDirection.UNKNOWN
    confidence: ParseConfidence = ParseConfidence.LOW
    parse_warnings: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)

    @property
    def measurement(self) -> str | None:
        return None if self.unit == WeatherUnit.UNKNOWN else self.unit.value


class WeatherSourceRecord(BaseModel):
    source_id: str
    market_id: str
    source_name: str
    source_type: SourceType
    city: str
    target_date: str
    fetched_at: str = Field(default_factory=now_iso)
    valid_time: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    normalized_value: float | None = None
    unit: WeatherUnit = WeatherUnit.UNKNOWN
    freshness_status: FreshnessStatus = FreshnessStatus.FRESH
    trust_level: TrustLevel = TrustLevel.PRIMARY


class EvidencePack(BaseModel):
    evidence_pack_id: str
    market_id: str
    descriptor: WeatherMarketDescriptor
    sources: list[WeatherSourceRecord] = Field(default_factory=list)
    evidence_freshness: EvidenceFreshness = EvidenceFreshness.MISSING
    evidence_conflict_level: EvidenceConflictLevel = EvidenceConflictLevel.NONE
    raw_refs: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)


class WeatherView(BaseModel):
    weather_view_id: str
    evidence_pack_id: str
    market_id: str
    city: str
    target_date: str
    expected_value: float
    expected_range_low: float
    expected_range_high: float
    sigma: float
    threshold: float | None = None
    direction: WeatherDirection = WeatherDirection.UNKNOWN
    unit: WeatherUnit = WeatherUnit.UNKNOWN
    confidence: ParseConfidence = ParseConfidence.LOW
    evidence_summary: list[str] = Field(default_factory=list)
    invalidation_rules: list[str] = Field(default_factory=list)
    confirmation_rules: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)


class ProbabilityView(BaseModel):
    probability_view_id: str
    weather_view_id: str
    market_id: str
    engine_id: str = "gaussian_v0"
    model_probability: float
    threshold: float | None = None
    expected_value: float
    sigma: float
    direction: WeatherDirection = WeatherDirection.UNKNOWN
    confidence: ParseConfidence = ParseConfidence.LOW
    warnings: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)
