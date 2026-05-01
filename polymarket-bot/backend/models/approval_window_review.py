from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from backend.models.core import now_iso


class ApprovalWindowReviewStatus(str, Enum):
    READY = "READY"
    PENDING = "PENDING"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


class ApprovalWindowState(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


class ApprovalWindowRecommendation(str, Enum):
    REVIEW_WINDOW = "REVIEW_WINDOW"
    REQUEST_APPROVAL = "REQUEST_APPROVAL"
    ACKNOWLEDGE_EXPIRY = "ACKNOWLEDGE_EXPIRY"
    OBSERVE_ONLY = "OBSERVE_ONLY"
    UNKNOWN = "UNKNOWN"


class ApprovalWindowReviewRecord(BaseModel):
    approval_window_review_id: str
    market_id: str
    decision_id: str
    candidate_id: str
    command_review_id: str | None = None
    execution_decision_review_id: str | None = None
    execution_queue_review_id: str | None = None
    approval_status: str | None = None
    approval_window_valid: bool | None = None
    approval_valid_until: str | None = None
    review_status: ApprovalWindowReviewStatus = ApprovalWindowReviewStatus.UNKNOWN
    window_state: ApprovalWindowState = ApprovalWindowState.UNKNOWN
    recommendation: ApprovalWindowRecommendation = ApprovalWindowRecommendation.UNKNOWN
    reviewed_at: str = Field(default_factory=now_iso)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApprovalWindowReviewSummary(BaseModel):
    approval_window_reviews: int = 0
    unique_markets: int = 0
    by_review_status: dict[str, int] = Field(default_factory=dict)
    by_window_state: dict[str, int] = Field(default_factory=dict)
    by_approval_status: dict[str, int] = Field(default_factory=dict)
    latest_reviewed_at: str | None = None


class ApprovalWindowReviewBundle(BaseModel):
    market_id: str
    approval_window_reviews: list[ApprovalWindowReviewRecord] = Field(default_factory=list)
