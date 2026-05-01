from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from backend.models.core import now_iso


class SampleEligibility(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


class CalibrationSampleStatus(str, Enum):
    READY = "READY"
    PENDING = "PENDING"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"


class BacktestMemoryStatus(str, Enum):
    READY = "READY"
    PENDING = "PENDING"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"


class HypotheticalAction(str, Enum):
    TAKE_YES = "TAKE_YES"
    TAKE_NO = "TAKE_NO"
    SKIP = "SKIP"
    UNKNOWN = "UNKNOWN"


class HypotheticalResult(str, Enum):
    WIN = "WIN"
    LOSS = "LOSS"
    PUSH = "PUSH"
    UNKNOWN = "UNKNOWN"


class ResolvedOutcomeForMemory(str, Enum):
    YES = "YES"
    NO = "NO"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNKNOWN = "UNKNOWN"


class CalibrationSample(BaseModel):
    calibration_sample_id: str
    market_id: str
    snapshot_archive_id: str | None = None
    weather_view_archive_id: str | None = None
    weather_forecast_archive_id: str | None = None
    probability_run_id: str | None = None
    outcome_resolution_id: str | None = None
    engine_id: str | None = None
    market_probability: float | None = None
    model_probability: float | None = None
    actual_outcome_value: float | None = None
    model_brier_score: float | None = None
    market_brier_score: float | None = None
    model_absolute_error: float | None = None
    market_absolute_error: float | None = None
    model_beats_market: bool | None = None
    resolved_outcome: ResolvedOutcomeForMemory = ResolvedOutcomeForMemory.UNKNOWN
    sample_eligibility: SampleEligibility = SampleEligibility.UNKNOWN
    sample_status: CalibrationSampleStatus = CalibrationSampleStatus.UNKNOWN
    sampled_at: str = Field(default_factory=now_iso)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BacktestMemoryRecord(BaseModel):
    backtest_memory_id: str
    market_id: str
    snapshot_archive_id: str | None = None
    weather_view_archive_id: str | None = None
    weather_forecast_archive_id: str | None = None
    probability_run_id: str | None = None
    outcome_resolution_id: str | None = None
    engine_id: str | None = None
    market_probability: float | None = None
    model_probability: float | None = None
    actual_outcome_value: float | None = None
    edge: float | None = None
    edge_threshold: float | None = None
    hypothetical_action: HypotheticalAction = HypotheticalAction.UNKNOWN
    hypothetical_result: HypotheticalResult = HypotheticalResult.UNKNOWN
    sample_eligibility: SampleEligibility = SampleEligibility.UNKNOWN
    backtest_status: BacktestMemoryStatus = BacktestMemoryStatus.UNKNOWN
    sampled_at: str = Field(default_factory=now_iso)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CalibrationMemorySummary(BaseModel):
    calibration_samples: int = 0
    backtest_memory_records: int = 0
    unique_markets: int = 0
    by_sample_status: dict[str, int] = Field(default_factory=dict)
    by_backtest_status: dict[str, int] = Field(default_factory=dict)
    by_eligibility: dict[str, int] = Field(default_factory=dict)
    latest_sampled_at: str | None = None


class CalibrationMemoryBundle(BaseModel):
    market_id: str
    calibration_samples: list[CalibrationSample] = Field(default_factory=list)
    backtest_memory_records: list[BacktestMemoryRecord] = Field(default_factory=list)
