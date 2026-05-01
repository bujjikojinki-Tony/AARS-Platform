from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from backend.models.core import now_iso


class ExecutionQueueReviewStatus(str, Enum):
    READY = "READY"
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class ExecutionQueueApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NOT_REQUIRED = "NOT_REQUIRED"
    UNKNOWN = "UNKNOWN"


class ExecutionQueueGateStatus(str, Enum):
    ALLOW = "ALLOW"
    BLOCKED = "BLOCKED"
    WARN = "WARN"
    UNKNOWN = "UNKNOWN"


class ExecutionQueueReviewRecommendation(str, Enum):
    REVIEW_QUEUE = "REVIEW_QUEUE"
    REVIEW_EXECUTION = "REVIEW_EXECUTION"
    REVIEW_GATE = "REVIEW_GATE"
    REQUEST_APPROVAL = "REQUEST_APPROVAL"
    BLOCK = "BLOCK"
    OBSERVE_ONLY = "OBSERVE_ONLY"
    UNKNOWN = "UNKNOWN"


class ExecutionQueueReviewRecord(BaseModel):
    execution_queue_review_id: str
    market_id: str
    decision_id: str
    candidate_id: str
    command_review_id: str | None = None
    execution_decision_review_id: str | None = None
    shadow_evaluation_id: str | None = None
    execution_mode: str | None = None
    action: str | None = None
    position_size: float | None = None
    expected_cost: float | None = None
    risk_status: str | None = None
    execution_status: str | None = None
    review_status: ExecutionQueueReviewStatus = ExecutionQueueReviewStatus.UNKNOWN
    approval_status: ExecutionQueueApprovalStatus = ExecutionQueueApprovalStatus.UNKNOWN
    gate_status: ExecutionQueueGateStatus = ExecutionQueueGateStatus.UNKNOWN
    recommendation: ExecutionQueueReviewRecommendation = ExecutionQueueReviewRecommendation.UNKNOWN
    approval_window_valid: bool | None = None
    approval_valid_until: str | None = None
    reviewed_at: str = Field(default_factory=now_iso)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionQueueReviewSummary(BaseModel):
    execution_queue_reviews: int = 0
    unique_markets: int = 0
    by_review_status: dict[str, int] = Field(default_factory=dict)
    by_approval_status: dict[str, int] = Field(default_factory=dict)
    by_gate_status: dict[str, int] = Field(default_factory=dict)
    by_execution_status: dict[str, int] = Field(default_factory=dict)
    by_execution_mode: dict[str, int] = Field(default_factory=dict)
    latest_reviewed_at: str | None = None


class ExecutionQueueReviewBundle(BaseModel):
    market_id: str
    execution_queue_reviews: list[ExecutionQueueReviewRecord] = Field(default_factory=list)
