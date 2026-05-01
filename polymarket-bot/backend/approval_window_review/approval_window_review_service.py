from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from backend.models.approval_window_review import ApprovalWindowRecommendation
from backend.models.approval_window_review import ApprovalWindowReviewBundle
from backend.models.approval_window_review import ApprovalWindowReviewRecord
from backend.models.approval_window_review import ApprovalWindowReviewStatus
from backend.models.approval_window_review import ApprovalWindowReviewSummary
from backend.models.approval_window_review import ApprovalWindowState


class ApprovalWindowReviewService:
    """
    Passive approval-window review service.

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
        execution_queue_review_id: str | None = None,
        raw_payload: dict | None = None,
        metadata: dict | None = None,
    ) -> ApprovalWindowReviewRecord:
        decision = self.repository.get_latest_execution_decision_for_market(market_id)
        if not decision:
            raise ValueError("latest execution decision not found")

        candidate = self.repository.get_candidate(str(decision.get("candidate_id") or ""))
        if not candidate:
            raise ValueError("latest candidate not found")

        command_review = self.repository.get_latest_command_review_for_market(market_id)
        execution_review = self.repository.get_latest_execution_decision_review_for_market(market_id)
        queue_review = (
            self.repository.get_latest_execution_queue_review_for_market(market_id)
            if execution_queue_review_id is None
            else self.repository.get_execution_queue_review_by_id(execution_queue_review_id)
        )
        if not queue_review:
            raise ValueError("latest execution queue review not found")

        approval_status = str(
            queue_review.get("approval_status")
            or execution_review.get("approval_status") if execution_review else ""
        ) or "UNKNOWN"
        approval_window_valid = queue_review.get("approval_window_valid")
        approval_valid_until = queue_review.get("approval_valid_until")
        window_state = self._derive_window_state(approval_window_valid, approval_valid_until)
        review_status = self._derive_review_status(window_state, approval_status)
        recommendation = self._derive_recommendation(window_state, approval_status)

        record = ApprovalWindowReviewRecord(
            approval_window_review_id=f"awr_{uuid4().hex[:12]}",
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
                else execution_queue_review_id
            ),
            approval_status=approval_status,
            approval_window_valid=approval_window_valid,
            approval_valid_until=approval_valid_until,
            review_status=review_status,
            window_state=window_state,
            recommendation=recommendation,
            raw_payload=raw_payload
            or {
                "decision": decision,
                "candidate": candidate,
                "command_review": command_review,
                "execution_review": execution_review,
                "queue_review": queue_review,
            },
            metadata=metadata or {"service": "ApprovalWindowReviewService"},
        )
        self.repository.save_approval_window_review_record(record)
        return record

    def build_all_eligible(self) -> list[ApprovalWindowReviewRecord]:
        records: list[ApprovalWindowReviewRecord] = []
        for market_id in self.repository.list_distinct_market_ids_for_approval_window_review():
            decision = self.repository.get_latest_execution_decision_for_market(market_id)
            queue_review = self.repository.get_latest_execution_queue_review_for_market(market_id)
            if not decision or not queue_review:
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
        review_status: str | None = None,
        window_state: str | None = None,
        approval_status: str | None = None,
    ) -> list[dict]:
        return self.repository.list_approval_window_review_records(
            limit=limit,
            market_id=market_id,
            review_status=review_status,
            window_state=window_state,
            approval_status=approval_status,
        )

    def get_market_bundle(self, market_id: str, limit: int = 100) -> ApprovalWindowReviewBundle:
        return self.repository.get_approval_window_review_bundle(market_id, limit=limit)

    def get_summary(self) -> ApprovalWindowReviewSummary:
        return self.repository.get_approval_window_review_summary()

    @staticmethod
    def _derive_window_state(approval_window_valid: object, approval_valid_until: object) -> ApprovalWindowState:
        if approval_valid_until:
            try:
                until_text = str(approval_valid_until).replace("Z", "+00:00")
                until_dt = datetime.fromisoformat(until_text)
                if until_dt.tzinfo is None:
                    until_dt = until_dt.replace(tzinfo=timezone.utc)
                if until_dt < datetime.now(timezone.utc):
                    return ApprovalWindowState.EXPIRED
            except ValueError:
                pass
        if approval_window_valid is True:
            return ApprovalWindowState.OPEN
        if approval_window_valid is False:
            return ApprovalWindowState.CLOSED
        return ApprovalWindowState.UNKNOWN

    @staticmethod
    def _derive_review_status(
        window_state: ApprovalWindowState,
        approval_status: str,
    ) -> ApprovalWindowReviewStatus:
        if window_state == ApprovalWindowState.EXPIRED:
            return ApprovalWindowReviewStatus.EXPIRED
        if window_state == ApprovalWindowState.OPEN and approval_status in {"APPROVED", "PENDING", "NOT_REQUIRED"}:
            return ApprovalWindowReviewStatus.READY
        if window_state == ApprovalWindowState.CLOSED or approval_status == "REJECTED":
            return ApprovalWindowReviewStatus.PENDING
        return ApprovalWindowReviewStatus.UNKNOWN

    @staticmethod
    def _derive_recommendation(
        window_state: ApprovalWindowState,
        approval_status: str,
    ) -> ApprovalWindowRecommendation:
        if window_state == ApprovalWindowState.EXPIRED:
            return ApprovalWindowRecommendation.ACKNOWLEDGE_EXPIRY
        if approval_status == "PENDING":
            return ApprovalWindowRecommendation.REQUEST_APPROVAL
        if approval_status == "NOT_REQUIRED":
            return ApprovalWindowRecommendation.OBSERVE_ONLY
        return ApprovalWindowRecommendation.REVIEW_WINDOW
