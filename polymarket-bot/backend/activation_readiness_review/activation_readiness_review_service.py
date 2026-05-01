from __future__ import annotations

from uuid import uuid4

from backend.models.activation_readiness_review import ActivationReadinessRecommendation
from backend.models.activation_readiness_review import ActivationReadinessReviewBundle
from backend.models.activation_readiness_review import ActivationReadinessReviewRecord
from backend.models.activation_readiness_review import ActivationReadinessReviewStatus
from backend.models.activation_readiness_review import ActivationReadinessReviewSummary


class ActivationReadinessReviewService:
    """
    Passive activation-readiness review service.

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
        approval_window_review_id: str | None = None,
        raw_payload: dict | None = None,
        metadata: dict | None = None,
    ) -> ActivationReadinessReviewRecord:
        decision = self.repository.get_latest_execution_decision_for_market(market_id)
        if not decision:
            raise ValueError("latest execution decision not found")

        candidate = self.repository.get_candidate(str(decision.get("candidate_id") or ""))
        if not candidate:
            raise ValueError("latest candidate not found")

        command_review = self.repository.get_latest_command_review_for_market(market_id)
        execution_review = self.repository.get_latest_execution_decision_review_for_market(market_id)
        queue_review = self.repository.get_latest_execution_queue_review_for_market(market_id)
        approval_review = (
            self.repository.get_latest_approval_window_review_for_market(market_id)
            if approval_window_review_id is None
            else self.repository.get_approval_window_review_by_id(approval_window_review_id)
        )
        if not approval_review:
            raise ValueError("latest approval window review not found")

        approval_status = str(approval_review.get("approval_status") or "UNKNOWN")
        window_state = str(approval_review.get("window_state") or "UNKNOWN")
        review_status = str(approval_review.get("review_status") or "UNKNOWN")
        readiness_status = self._derive_readiness_status(
            approval_status=approval_status,
            window_state=window_state,
            review_status=review_status,
        )
        recommendation = self._derive_recommendation(
            approval_status=approval_status,
            window_state=window_state,
            review_status=review_status,
            readiness_status=readiness_status,
        )

        record = ActivationReadinessReviewRecord(
            activation_readiness_review_id=f"arr_{uuid4().hex[:12]}",
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
                else approval_window_review_id
            ),
            approval_status=approval_status,
            window_state=window_state,
            review_status=review_status,
            readiness_status=readiness_status,
            recommendation=recommendation,
            raw_payload=raw_payload
            or {
                "decision": decision,
                "candidate": candidate,
                "command_review": command_review,
                "execution_review": execution_review,
                "queue_review": queue_review,
                "approval_review": approval_review,
            },
            metadata=metadata or {"service": "ActivationReadinessReviewService"},
        )
        self.repository.save_activation_readiness_review_record(record)
        return record

    def build_all_eligible(self) -> list[ActivationReadinessReviewRecord]:
        records: list[ActivationReadinessReviewRecord] = []
        for market_id in self.repository.list_distinct_market_ids_for_activation_readiness_review():
            decision = self.repository.get_latest_execution_decision_for_market(market_id)
            approval_review = self.repository.get_latest_approval_window_review_for_market(market_id)
            if not decision or not approval_review:
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
        readiness_status: str | None = None,
        recommendation: str | None = None,
        approval_status: str | None = None,
    ) -> list[dict]:
        return self.repository.list_activation_readiness_review_records(
            limit=limit,
            market_id=market_id,
            readiness_status=readiness_status,
            recommendation=recommendation,
            approval_status=approval_status,
        )

    def get_market_bundle(self, market_id: str, limit: int = 100) -> ActivationReadinessReviewBundle:
        return self.repository.get_activation_readiness_review_bundle(market_id, limit=limit)

    def get_summary(self) -> ActivationReadinessReviewSummary:
        return self.repository.get_activation_readiness_review_summary()

    @staticmethod
    def _derive_readiness_status(
        *,
        approval_status: str,
        window_state: str,
        review_status: str,
    ) -> ActivationReadinessReviewStatus:
        if window_state == "EXPIRED":
            return ActivationReadinessReviewStatus.NOT_READY
        if approval_status == "REJECTED":
            return ActivationReadinessReviewStatus.NOT_READY
        if approval_status == "APPROVED" and window_state == "OPEN" and review_status == "READY":
            return ActivationReadinessReviewStatus.READY
        if approval_status in {"PENDING", "UNKNOWN"} or review_status in {"PENDING", "UNKNOWN"}:
            return ActivationReadinessReviewStatus.NEEDS_REVIEW
        return ActivationReadinessReviewStatus.UNKNOWN

    @staticmethod
    def _derive_recommendation(
        *,
        approval_status: str,
        window_state: str,
        review_status: str,
        readiness_status: ActivationReadinessReviewStatus,
    ) -> ActivationReadinessRecommendation:
        if readiness_status == ActivationReadinessReviewStatus.READY:
            return ActivationReadinessRecommendation.READY_FOR_GOVERNED_REVIEW
        if approval_status == "PENDING":
            return ActivationReadinessRecommendation.REQUEST_APPROVAL
        if window_state == "EXPIRED" or approval_status == "REJECTED":
            return ActivationReadinessRecommendation.HOLD_OBSERVE_ONLY
        if review_status in {"PENDING", "UNKNOWN"}:
            return ActivationReadinessRecommendation.REVIEW_GOVERNANCE
        return ActivationReadinessRecommendation.UNKNOWN
