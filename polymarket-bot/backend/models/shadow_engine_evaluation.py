from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from backend.models.core import now_iso


class ShadowEvaluationStatus(str, Enum):
    READY = "READY"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"


class BestShadowEngine(str, Enum):
    GAUSSIAN = "GAUSSIAN"
    DEB_SHADOW = "DEB_SHADOW"
    EMOS_SHADOW = "EMOS_SHADOW"
    TIE = "TIE"
    UNKNOWN = "UNKNOWN"


class ShadowEngineEvaluationRecord(BaseModel):
    shadow_evaluation_id: str
    market_id: str
    calibration_sample_id: str | None = None
    outcome_resolution_id: str | None = None
    primary_engine_id: str = "gaussian_v0"
    deb_engine_id: str = "deb_shadow_v1"
    emos_engine_id: str = "emos_shadow_v1"
    primary_probability: float | None = None
    deb_probability: float | None = None
    emos_probability: float | None = None
    actual_outcome_value: float | None = None
    primary_brier_score: float | None = None
    deb_brier_score: float | None = None
    emos_brier_score: float | None = None
    primary_absolute_error: float | None = None
    deb_absolute_error: float | None = None
    emos_absolute_error: float | None = None
    best_engine: BestShadowEngine = BestShadowEngine.UNKNOWN
    evaluation_status: ShadowEvaluationStatus = ShadowEvaluationStatus.UNKNOWN
    created_at: str = Field(default_factory=now_iso)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ShadowEngineEvaluationSummary(BaseModel):
    total_evaluations: int = 0
    unique_markets: int = 0
    by_status: dict[str, int] = Field(default_factory=dict)
    by_best_engine: dict[str, int] = Field(default_factory=dict)
    latest_created_at: str | None = None


class ShadowEngineEvaluationBundle(BaseModel):
    market_id: str
    evaluations: list[ShadowEngineEvaluationRecord] = Field(default_factory=list)
