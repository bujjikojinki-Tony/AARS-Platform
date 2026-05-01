from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from backend.models.core import now_iso


class EmosShadowRunStatus(str, Enum):
    READY = "READY"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"


class EmosShadowRunRecord(BaseModel):
    emos_shadow_run_id: str
    market_id: str
    calibration_sample_id: str | None = None
    engine_id: str = "emos_shadow_v1"
    base_probability: float | None = None
    emos_probability: float | None = None
    location_adjustment: float | None = None
    scale_adjustment: float | None = None
    sample_count: int = 0
    run_status: EmosShadowRunStatus = EmosShadowRunStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmosShadowDiagnosticRecord(BaseModel):
    emos_shadow_diagnostic_id: str
    emos_shadow_run_id: str
    market_id: str
    calibration_sample_id: str | None = None
    sample_count: int = 0
    avg_model_brier_score: float | None = None
    avg_market_brier_score: float | None = None
    avg_probability_error: float | None = None
    avg_absolute_error: float | None = None
    location_weight: float | None = None
    scale_weight: float | None = None
    notes: str | None = None
    created_at: str = Field(default_factory=now_iso)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmosShadowSummary(BaseModel):
    total_runs: int = 0
    total_diagnostics: int = 0
    unique_markets: int = 0
    by_run_status: dict[str, int] = Field(default_factory=dict)
    latest_created_at: str | None = None


class EmosShadowMarketBundle(BaseModel):
    market_id: str
    runs: list[EmosShadowRunRecord] = Field(default_factory=list)
    diagnostics: list[EmosShadowDiagnosticRecord] = Field(default_factory=list)
