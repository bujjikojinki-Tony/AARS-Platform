from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from backend.models.core import now_iso


class CommandReviewStatus(str, Enum):
    READY = "READY"
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class CommandApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NOT_REQUIRED = "NOT_REQUIRED"
    UNKNOWN = "UNKNOWN"


class CommandGateStatus(str, Enum):
    ALLOW = "ALLOW"
    BLOCKED = "BLOCKED"
    WARN = "WARN"
    UNKNOWN = "UNKNOWN"


class CommandReviewRecommendation(str, Enum):
    OPEN_WORKSTATION = "OPEN_WORKSTATION"
    REVIEW_EVIDENCE = "REVIEW_EVIDENCE"
    CREATE_PENDING_INTENT = "CREATE_PENDING_INTENT"
    RUN_DRY_RUN_CHECK = "RUN_DRY_RUN_CHECK"
    REQUEST_APPROVAL = "REQUEST_APPROVAL"
    BLOCK = "BLOCK"
    MUTE_SIGNAL = "MUTE_SIGNAL"
    UNKNOWN = "UNKNOWN"


class CommandReviewRecord(BaseModel):
    command_review_id: str
    market_id: str
    command_name: str
    source_page: str
    target_page: str | None = None
    command_path: str | None = None
    review_status: CommandReviewStatus = CommandReviewStatus.UNKNOWN
    approval_status: CommandApprovalStatus = CommandApprovalStatus.UNKNOWN
    recommendation: CommandReviewRecommendation = CommandReviewRecommendation.UNKNOWN
    gate_status: CommandGateStatus = CommandGateStatus.UNKNOWN
    active_engine_id: str | None = None
    execution_mode: str | None = None
    risk_status: str | None = None
    approval_window_valid: bool | None = None
    approval_valid_until: str | None = None
    market_snapshot_archive_id: str | None = None
    weather_view_archive_id: str | None = None
    weather_forecast_archive_id: str | None = None
    probability_run_id: str | None = None
    outcome_resolution_id: str | None = None
    calibration_sample_id: str | None = None
    backtest_memory_id: str | None = None
    deb_shadow_run_id: str | None = None
    emos_shadow_run_id: str | None = None
    shadow_evaluation_id: str | None = None
    reviewed_at: str = Field(default_factory=now_iso)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommandReviewSummary(BaseModel):
    command_reviews: int = 0
    unique_markets: int = 0
    by_review_status: dict[str, int] = Field(default_factory=dict)
    by_approval_status: dict[str, int] = Field(default_factory=dict)
    by_gate_status: dict[str, int] = Field(default_factory=dict)
    latest_reviewed_at: str | None = None


class CommandReviewBundle(BaseModel):
    market_id: str
    command_reviews: list[CommandReviewRecord] = Field(default_factory=list)
