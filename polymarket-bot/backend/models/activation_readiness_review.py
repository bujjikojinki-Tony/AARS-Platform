from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from backend.models.core import now_iso


class ActivationReadinessReviewStatus(str, Enum):
    READY = "READY"
    NOT_READY = "NOT_READY"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    UNKNOWN = "UNKNOWN"


class ActivationReadinessRecommendation(str, Enum):
    READY_FOR_GOVERNED_REVIEW = "READY_FOR_GOVERNED_REVIEW"
    REQUEST_APPROVAL = "REQUEST_APPROVAL"
    HOLD_OBSERVE_ONLY = "HOLD_OBSERVE_ONLY"
    REVIEW_GOVERNANCE = "REVIEW_GOVERNANCE"
    UNKNOWN = "UNKNOWN"


class ActivationReadinessReviewRecord(BaseModel):
    activation_readiness_review_id: str
    market_id: str
    decision_id: str
    candidate_id: str
    command_review_id: str | None = None
    execution_decision_review_id: str | None = None
    execution_queue_review_id: str | None = None
    approval_window_review_id: str | None = None
    approval_status: str | None = None
    window_state: str | None = None
    review_status: str | None = None
    readiness_status: ActivationReadinessReviewStatus = ActivationReadinessReviewStatus.UNKNOWN
    recommendation: ActivationReadinessRecommendation = ActivationReadinessRecommendation.UNKNOWN
    reviewed_at: str = Field(default_factory=now_iso)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ActivationReadinessReviewSummary(BaseModel):
    activation_readiness_reviews: int = 0
    unique_markets: int = 0
    by_readiness_status: dict[str, int] = Field(default_factory=dict)
    by_recommendation: dict[str, int] = Field(default_factory=dict)
    by_approval_status: dict[str, int] = Field(default_factory=dict)
    latest_reviewed_at: str | None = None


class ActivationReadinessReviewBundle(BaseModel):
    market_id: str
    activation_readiness_reviews: list[ActivationReadinessReviewRecord] = Field(default_factory=list)
