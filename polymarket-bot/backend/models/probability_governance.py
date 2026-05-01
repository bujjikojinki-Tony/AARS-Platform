from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from backend.models.core import now_iso


class ProbabilityEngineType(str, Enum):
    PRIMARY = "PRIMARY"
    SHADOW = "SHADOW"
    DISABLED = "DISABLED"


class DisagreementLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class OutcomeStatus(str, Enum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    DISPUTED = "DISPUTED"
    UNKNOWN = "UNKNOWN"


class PromotionDecisionType(str, Enum):
    PROMOTE = "PROMOTE"
    KEEP_SHADOW = "KEEP_SHADOW"
    DISABLE = "DISABLE"
    NEEDS_MORE_DATA = "NEEDS_MORE_DATA"
    KEEP_PRIMARY = "KEEP_PRIMARY"


class ProbabilityEngineConfig(BaseModel):
    engine_id: str
    engine_name: str
    engine_type: ProbabilityEngineType
    version: str = "v0"
    enabled: bool = True
    can_be_primary: bool = False
    description: str = ""
    default_params: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class ProbabilityEngineRun(BaseModel):
    run_id: str
    market_id: str
    weather_view_id: str
    engine_id: str
    engine_type: ProbabilityEngineType
    model_probability: float
    expected_value: Optional[float] = None
    sigma: Optional[float] = None
    threshold: Optional[float] = None
    direction: Optional[str] = None
    params: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)


class ProbabilityComparisonView(BaseModel):
    comparison_id: str
    market_id: str
    weather_view_id: str
    active_engine_id: str
    active_probability: float
    engine_runs: list[ProbabilityEngineRun] = Field(default_factory=list)
    spread_between_engines: float
    disagreement_level: DisagreementLevel
    selection_reason: str
    warnings: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)


class MarketOutcome(BaseModel):
    outcome_id: str
    market_id: str
    resolved_value: Optional[float] = None
    resolved_direction_hit: Optional[bool] = None
    official_source: Optional[str] = None
    resolved_at: str = Field(default_factory=now_iso)
    status: OutcomeStatus = OutcomeStatus.PENDING
    notes: Optional[str] = None


class CalibrationResult(BaseModel):
    calibration_id: str
    market_id: str
    engine_id: str
    run_id: str
    outcome_id: str
    predicted_probability: float
    actual_outcome: int
    brier_score: float
    absolute_error: float
    bucket: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)


class EnginePromotionDecision(BaseModel):
    decision_id: str
    engine_id: str
    current_type: ProbabilityEngineType
    proposed_type: ProbabilityEngineType
    eligible: bool
    decision: PromotionDecisionType
    evidence_count: int
    avg_brier_score: Optional[float] = None
    avg_absolute_error: Optional[float] = None
    reason: str
    created_at: str = Field(default_factory=now_iso)
