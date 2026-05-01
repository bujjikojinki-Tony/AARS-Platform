from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from backend.models.core import now_iso


class ActivationAuthorizationReviewStatus(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    NEEDS_AUTHORIZATION = "NEEDS_AUTHORIZATION"
    UNKNOWN = "UNKNOWN"


class ActivationAuthorizationRecommendation(str, Enum):
    READY_FOR_AUTHORIZATION_REVIEW = "READY_FOR_AUTHORIZATION_REVIEW"
    REQUEST_AUTHORIZATION = "REQUEST_AUTHORIZATION"
    HOLD_OBSERVE_ONLY = "HOLD_OBSERVE_ONLY"
    REVIEW_AUTHORIZATION = "REVIEW_AUTHORIZATION"
    UNKNOWN = "UNKNOWN"


class ActivationAuthorizationReviewRecord(BaseModel):
    activation_authorization_review_id: str
    market_id: str
    decision_id: str
    candidate_id: str
    command_review_id: str | None = None
    execution_decision_review_id: str | None = None
    execution_queue_review_id: str | None = None
    approval_window_review_id: str | None = None
    activation_readiness_review_id: str | None = None
    approval_status: str | None = None
    window_state: str | None = None
    readiness_status: str | None = None
    authorization_status: ActivationAuthorizationReviewStatus = ActivationAuthorizationReviewStatus.UNKNOWN
    recommendation: ActivationAuthorizationRecommendation = ActivationAuthorizationRecommendation.UNKNOWN
    reviewed_at: str = Field(default_factory=now_iso)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ActivationAuthorizationReviewSummary(BaseModel):
    activation_authorization_reviews: int = 0
    unique_markets: int = 0
    by_authorization_status: dict[str, int] = Field(default_factory=dict)
    by_recommendation: dict[str, int] = Field(default_factory=dict)
    by_approval_status: dict[str, int] = Field(default_factory=dict)
    latest_reviewed_at: str | None = None


class ActivationAuthorizationReviewBundle(BaseModel):
    market_id: str
    activation_authorization_reviews: list[ActivationAuthorizationReviewRecord] = Field(default_factory=list)
