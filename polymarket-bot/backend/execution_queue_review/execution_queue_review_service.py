from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.models.command_review import CommandReviewStatus
from backend.models.enums import ExecutionMode
from backend.models.enums import ExecutionStatus
from backend.models.enums import RiskStatus
from backend.models.execution_queue_review import ExecutionQueueApprovalStatus
from backend.models.execution_queue_review import ExecutionQueueGateStatus
from backend.models.execution_queue_review import ExecutionQueueReviewBundle
from backend.models.execution_queue_review import ExecutionQueueReviewRecommendation
from backend.models.execution_queue_review import ExecutionQueueReviewRecord
from backend.models.execution_queue_review import ExecutionQueueReviewStatus
from backend.models.execution_queue_review import ExecutionQueueReviewSummary


class ExecutionQueueReviewService:
    """
    Passive execution queue review service.

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
        execution_decision_review_id: str | None = None,
        raw_payload: dict | None = None,
        metadata: dict | None = None,
    ) -> ExecutionQueueReviewRecord:
        decision = self.repository.get_latest_execution_decision_for_market(market_id)
        if not decision:
            raise ValueError("latest execution decision not found")

        candidate = self.repository.get_candidate(str(decision.get("candidate_id") or ""))
        if not candidate:
            raise ValueError("latest candidate not found")

        command_review = self.repository.get_latest_command_review_for_market(market_id)
        execution_review = (
            self.repository.get_latest_execution_decision_review_for_market(market_id)
            if execution_decision_review_id is None
            else self.repository.get_execution_decision_review_by_id(execution_decision_review_id)
        )
        shadow_eval = self.repository.get_latest_shadow_engine_evaluation_for_market(market_id)
        outcome_resolution = self.repository.get_latest_outcome_resolution_for_market(market_id)
        calibration_sample = self.repository.get_latest_calibration_sample_for_market(market_id)
        snapshot = self.repository.get_latest_market_snapshot_archive_for_market(market_id)
        weather_view = self.repository.get_latest_weather_view_archive_for_market(market_id)
        weather_forecast = self.repository.get_latest_weather_forecast_archive_for_market(market_id)

        execution_mode = str(decision.get("mode") or ExecutionMode.OBSERVE_ONLY.value)
        execution_status = str(decision.get("execution_status") or ExecutionStatus.QUEUED.value)
        risk_status = str(decision.get("risk_status") or RiskStatus.WARN.value)
        complete_context = all(
            [
                decision is not None,
                candidate is not None,
                command_review is not None,
                execution_review is not None,
                shadow_eval is not None,
                outcome_resolution is not None,
                calibration_sample is not None,
                snapshot is not None,
                weather_view is not None,
                weather_forecast is not None,
            ]
        )

        gate_status = self._derive_gate_status(
            execution_mode=execution_mode,
            execution_status=execution_status,
            risk_status=risk_status,
            complete_context=complete_context,
        )
        review_status = (
            ExecutionQueueReviewStatus.READY
            if gate_status == ExecutionQueueGateStatus.ALLOW and execution_status == ExecutionStatus.QUEUED.value
            else ExecutionQueueReviewStatus.PENDING
        )
        if execution_status == ExecutionStatus.FAILED.value or risk_status == RiskStatus.BLOCK.value:
            review_status = ExecutionQueueReviewStatus.BLOCKED

        recommendation = self._derive_recommendation(
            execution_mode=execution_mode,
            gate_status=gate_status,
            execution_status=execution_status,
            risk_status=risk_status,
            command_review=command_review,
            execution_review=execution_review,
        )

        record = ExecutionQueueReviewRecord(
            execution_queue_review_id=f"eqr_{uuid4().hex[:12]}",
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
                else execution_decision_review_id
            ),
            shadow_evaluation_id=(
                str(shadow_eval.get("shadow_evaluation_id"))
                if isinstance(shadow_eval, dict) and shadow_eval.get("shadow_evaluation_id")
                else None
            ),
            execution_mode=execution_mode,
            action=str(decision.get("action") or "review"),
            position_size=self._as_float(decision.get("position_size")),
            expected_cost=self._as_float(decision.get("expected_cost")),
            risk_status=risk_status,
            execution_status=execution_status,
            review_status=review_status,
            approval_status=(
                ExecutionQueueApprovalStatus.NOT_REQUIRED
                if execution_mode == ExecutionMode.OBSERVE_ONLY.value and gate_status == ExecutionQueueGateStatus.ALLOW
                else ExecutionQueueApprovalStatus.PENDING
            ),
            gate_status=gate_status,
            recommendation=recommendation,
            approval_window_valid=gate_status == ExecutionQueueGateStatus.ALLOW,
            approval_valid_until=self._next_approval_window(),
            raw_payload=raw_payload
            or {
                "complete_context": complete_context,
                "decision": decision,
                "candidate": candidate,
                "command_review": command_review,
                "execution_review": execution_review,
                "shadow_evaluation": shadow_eval,
                "snapshot": snapshot,
                "weather_view": weather_view,
                "weather_forecast": weather_forecast,
                "outcome_resolution": outcome_resolution,
                "calibration_sample": calibration_sample,
            },
            metadata=metadata or {"service": "ExecutionQueueReviewService"},
        )
        self.repository.save_execution_queue_review_record(record)
        return record

    def build_all_eligible(self) -> list[ExecutionQueueReviewRecord]:
        records: list[ExecutionQueueReviewRecord] = []
        for market_id in self.repository.list_distinct_market_ids_for_execution_queue_review():
            decision = self.repository.get_latest_execution_decision_for_market(market_id)
            if not decision:
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
        approval_status: str | None = None,
        gate_status: str | None = None,
        execution_status: str | None = None,
        execution_mode: str | None = None,
    ) -> list[dict]:
        return self.repository.list_execution_queue_review_records(
            limit=limit,
            market_id=market_id,
            review_status=review_status,
            approval_status=approval_status,
            gate_status=gate_status,
            execution_status=execution_status,
            execution_mode=execution_mode,
        )

    def get_market_bundle(self, market_id: str, limit: int = 100) -> ExecutionQueueReviewBundle:
        return self.repository.get_execution_queue_review_bundle(market_id, limit=limit)

    def get_summary(self) -> ExecutionQueueReviewSummary:
        return self.repository.get_execution_queue_review_summary()

    def _derive_gate_status(
        self,
        *,
        execution_mode: str,
        execution_status: str,
        risk_status: str,
        complete_context: bool,
    ) -> ExecutionQueueGateStatus:
        if execution_status == ExecutionStatus.FAILED.value or risk_status == RiskStatus.BLOCK.value:
            return ExecutionQueueGateStatus.BLOCKED
        if execution_mode == ExecutionMode.LIVE_EXECUTE.value:
            return ExecutionQueueGateStatus.BLOCKED
        if execution_mode in {ExecutionMode.SIMULATION.value, ExecutionMode.PAPER_TRADE.value}:
            return ExecutionQueueGateStatus.WARN
        return ExecutionQueueGateStatus.ALLOW if complete_context else ExecutionQueueGateStatus.WARN

    def _derive_recommendation(
        self,
        *,
        execution_mode: str,
        gate_status: ExecutionQueueGateStatus,
        execution_status: str,
        risk_status: str,
        command_review: dict | None,
        execution_review: dict | None,
    ) -> ExecutionQueueReviewRecommendation:
        if execution_status == ExecutionStatus.FAILED.value or risk_status == RiskStatus.BLOCK.value:
            return ExecutionQueueReviewRecommendation.BLOCK
        if execution_mode == ExecutionMode.LIVE_EXECUTE.value:
            return ExecutionQueueReviewRecommendation.REQUEST_APPROVAL
        if command_review and command_review.get("review_status") == CommandReviewStatus.BLOCKED.value:
            return ExecutionQueueReviewRecommendation.REVIEW_GATE
        if execution_review and execution_review.get("review_status") == "BLOCKED":
            return ExecutionQueueReviewRecommendation.REVIEW_GATE
        if execution_mode == ExecutionMode.OBSERVE_ONLY.value:
            return ExecutionQueueReviewRecommendation.OBSERVE_ONLY
        if gate_status == ExecutionQueueGateStatus.ALLOW:
            return ExecutionQueueReviewRecommendation.REVIEW_EXECUTION
        return ExecutionQueueReviewRecommendation.REVIEW_QUEUE

    @staticmethod
    def _as_float(value: object) -> float:
        if value is None:
            return 0.0
        return float(value)

    @staticmethod
    def _next_approval_window() -> str:
        return (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
