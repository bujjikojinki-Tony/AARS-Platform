from __future__ import annotations

from uuid import uuid4

from backend.models.activation_authorization_review import ActivationAuthorizationRecommendation
from backend.models.activation_authorization_review import ActivationAuthorizationReviewBundle
from backend.models.activation_authorization_review import ActivationAuthorizationReviewRecord
from backend.models.activation_authorization_review import ActivationAuthorizationReviewStatus
from backend.models.activation_authorization_review import ActivationAuthorizationReviewSummary


class ActivationAuthorizationReviewService:
    """
    Passive activation-authorization review service.

    Safety boundary:
    - Does not call StrategyRunner.
    - Does not call Simulator.
    - Does not call execution.
    - Does not call promotion gates.
    - Does not call trading logic.
    """

    def __init__(self, repository):
        self.repository = repository

    def build_for_market(
        self,
        market_id: str,
        *,
        activation_readiness_review_id: str | None = None,
        raw_payload: dict | None = None,
        metadata: dict | None = None,
    ) -> ActivationAuthorizationReviewRecord:
        decision = self.repository.get_latest_execution_decision_for_market(market_id)
        if not decision:
            raise ValueError("latest execution decision not found")

        candidate = self.repository.get_candidate(str(decision.get("candidate_id") or ""))
        if not candidate:
            raise ValueError("latest candidate not found")

        command_review = self.repository.get_latest_command_review_for_market(market_id)
        execution_review = self.repository.get_latest_execution_decision_review_for_market(market_id)
        queue_review = self.repository.get_latest_execution_queue_review_for_market(market_id)
        approval_review = self.repository.get_latest_approval_window_review_for_market(market_id)
        readiness_review = (
            self.repository.get_latest_activation_readiness_review_for_market(market_id)
            if activation_readiness_review_id is None
            else self.repository.get_activation_readiness_review_by_id(activation_readiness_review_id)
        )
        if not readiness_review:
            raise ValueError("latest activation readiness review not found")

        approval_status = str(
            readiness_review.get("approval_status")
            or (approval_review.get("approval_status") if isinstance(approval_review, dict) else "")
            or "UNKNOWN"
        )
        window_state = str(
            readiness_review.get("window_state")
            or (approval_review.get("window_state") if isinstance(approval_review, dict) else "")
            or "UNKNOWN"
        )
        readiness_status = str(readiness_review.get("readiness_status") or "UNKNOWN")
        authorization_status = self._derive_authorization_status(
            approval_status=approval_status,
            window_state=window_state,
            readiness_status=readiness_status,
        )
        recommendation = self._derive_recommendation(
            approval_status=approval_status,
            window_state=window_state,
            readiness_status=readiness_status,
            authorization_status=authorization_status,
        )

        record = ActivationAuthorizationReviewRecord(
            activation_authorization_review_id=f"aar_{uuid4().hex[:12]}",
            market_id=market_id,
            decision_id=str(decision.get("decision_id")),
            candidate_id=str(decision.get("candidate_id")),
            command_review_id=(
                str(command_review.get("command_review_id"))
                if isinstance(command_review, dict) and command_review.get("command_review_id")
                else None
            ),
            execution_decision_review_id=(
                str(execution_review.get("execution_decision_review_id"))
                if isinstance(execution_review, dict) and execution_review.get("execution_decision_review_id")
                else None
            ),
            execution_queue_review_id=(
                str(queue_review.get("execution_queue_review_id"))
                if isinstance(queue_review, dict) and queue_review.get("execution_queue_review_id")
                else None
            ),
            approval_window_review_id=(
                str(approval_review.get("approval_window_review_id"))
                if isinstance(approval_review, dict) and approval_review.get("approval_window_review_id")
                else None
            ),
            activation_readiness_review_id=(
                str(readiness_review.get("activation_readiness_review_id"))
                if isinstance(readiness_review, dict) and readiness_review.get("activation_readiness_review_id")
                else activation_readiness_review_id
            ),
            approval_status=approval_status,
            window_state=window_state,
            readiness_status=readiness_status,
            authorization_status=authorization_status,
            recommendation=recommendation,
            raw_payload=raw_payload
            or {
                "decision": decision,
                "candidate": candidate,
                "command_review": command_review,
                "execution_review": execution_review,
                "queue_review": queue_review,
                "approval_review": approval_review,
                "readiness_review": readiness_review,
            },
            metadata=metadata or {"service": "ActivationAuthorizationReviewService"},
        )
        self.repository.save_activation_authorization_review_record(record)
        return record

    def build_all_eligible(self) -> list[ActivationAuthorizationReviewRecord]:
        records: list[ActivationAuthorizationReviewRecord] = []
        for market_id in self.repository.list_distinct_market_ids_for_activation_authorization_review():
            decision = self.repository.get_latest_execution_decision_for_market(market_id)
            readiness_review = self.repository.get_latest_activation_readiness_review_for_market(market_id)
            if not decision or not readiness_review:
                continue
            if not self.repository.get_candidate(str(decision.get("candidate_id") or "")):
                continue
            try:
                records.append(self.build_for_market(market_id))
            except ValueError:
                continue
        return records

    def list_reviews(
        self,
        limit: int = 100,
        market_id: str | None = None,
        authorization_status: str | None = None,
        recommendation: str | None = None,
        approval_status: str | None = None,
    ) -> list[dict]:
        return self.repository.list_activation_authorization_review_records(
            limit=limit,
            market_id=market_id,
            authorization_status=authorization_status,
            recommendation=recommendation,
            approval_status=approval_status,
        )

    def get_market_bundle(self, market_id: str, limit: int = 100) -> ActivationAuthorizationReviewBundle:
        return self.repository.get_activation_authorization_review_bundle(market_id, limit=limit)

    def get_summary(self) -> ActivationAuthorizationReviewSummary:
        return self.repository.get_activation_authorization_review_summary()

    @staticmethod
    def _derive_authorization_status(
        *,
        approval_status: str,
        window_state: str,
        readiness_status: str,
    ) -> ActivationAuthorizationReviewStatus:
        if readiness_status == "READY" and approval_status == "APPROVED" and window_state == "OPEN":
            return ActivationAuthorizationReviewStatus.AUTHORIZED
        if window_state == "EXPIRED" or approval_status == "REJECTED" or readiness_status == "NOT_READY":
            return ActivationAuthorizationReviewStatus.NOT_AUTHORIZED
        if approval_status in {"PENDING", "UNKNOWN"} or readiness_status in {"NEEDS_REVIEW", "UNKNOWN"}:
            return ActivationAuthorizationReviewStatus.NEEDS_AUTHORIZATION
        return ActivationAuthorizationReviewStatus.UNKNOWN

    @staticmethod
    def _derive_recommendation(
        *,
        approval_status: str,
        window_state: str,
        readiness_status: str,
        authorization_status: ActivationAuthorizationReviewStatus,
    ) -> ActivationAuthorizationRecommendation:
        if authorization_status == ActivationAuthorizationReviewStatus.AUTHORIZED:
            return ActivationAuthorizationRecommendation.READY_FOR_AUTHORIZATION_REVIEW
        if approval_status == "PENDING":
            return ActivationAuthorizationRecommendation.REQUEST_AUTHORIZATION
        if window_state == "EXPIRED" or approval_status == "REJECTED" or readiness_status == "NOT_READY":
            return ActivationAuthorizationRecommendation.HOLD_OBSERVE_ONLY
        if readiness_status in {"NEEDS_REVIEW", "UNKNOWN"}:
            return ActivationAuthorizationRecommendation.REVIEW_AUTHORIZATION
        return ActivationAuthorizationRecommendation.UNKNOWN
