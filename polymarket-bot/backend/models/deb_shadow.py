from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from backend.models.core import now_iso


class DebShadowRunStatus(str, Enum):
    READY = "READY"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"


class DebShadowRunRecord(BaseModel):
    deb_shadow_run_id: str
    market_id: str
    calibration_sample_id: str | None = None
    engine_id: str = "deb_shadow_v1"
    base_probability: float | None = None
    deb_probability: float | None = None
    bias_adjustment: float | None = None
    calibration_gap: float | None = None
    sample_count: int = 0
    run_status: DebShadowRunStatus = DebShadowRunStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DebShadowDiagnosticRecord(BaseModel):
    deb_shadow_diagnostic_id: str
    deb_shadow_run_id: str
    market_id: str
    calibration_sample_id: str | None = None
    sample_count: int = 0
    avg_model_brier_score: float | None = None
    avg_market_brier_score: float | None = None
    avg_model_edge: float | None = None
    avg_probability_error: float | None = None
    adjustment_weight: float | None = None
    notes: str | None = None
    created_at: str = Field(default_factory=now_iso)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DebShadowSummary(BaseModel):
    total_runs: int = 0
    total_diagnostics: int = 0
    unique_markets: int = 0
    by_run_status: dict[str, int] = Field(default_factory=dict)
    latest_created_at: str | None = None


class DebShadowMarketBundle(BaseModel):
    market_id: str
    runs: list[DebShadowRunRecord] = Field(default_factory=list)
    diagnostics: list[DebShadowDiagnosticRecord] = Field(default_factory=list)
