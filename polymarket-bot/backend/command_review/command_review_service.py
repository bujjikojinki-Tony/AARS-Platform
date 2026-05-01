from __future__ import annotations

from uuid import uuid4

from backend.models.command_review import CommandApprovalStatus
from backend.models.command_review import CommandGateStatus
from backend.models.command_review import CommandReviewBundle
from backend.models.command_review import CommandReviewRecommendation
from backend.models.command_review import CommandReviewRecord
from backend.models.command_review import CommandReviewStatus
from backend.models.command_review import CommandReviewSummary


class CommandReviewService:
    """
    Passive command review service.

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
        command_name: str = "/review",
        source_page: str = "command",
        target_page: str = "history",
        command_path: str = "/api/command-review/build",
        approval_status: str | CommandApprovalStatus | None = None,
        review_status: str | CommandReviewStatus | None = None,
        recommendation: str | CommandReviewRecommendation | None = None,
        metadata: dict | None = None,
        raw_payload: dict | None = None,
    ) -> CommandReviewRecord:
        snapshot = self.repository.get_latest_market_snapshot_archive_for_market(market_id)
        weather_view = self.repository.get_latest_weather_view_archive_for_market(market_id)
        weather_forecast = self.repository.get_latest_weather_forecast_archive_for_market(market_id)
        probability_run = self.repository.get_latest_probability_engine_run_for_market(market_id)
        outcome_resolution = self.repository.get_latest_outcome_resolution_for_market(market_id)
        calibration_sample = self.repository.get_latest_calibration_sample_for_market(market_id)
        backtest_memory = self.repository.get_latest_backtest_memory_for_market(market_id)
        deb_shadow_run = self.repository.get_latest_deb_shadow_run_for_market(market_id)
        emos_shadow_run = self.repository.get_latest_emos_shadow_run_for_market(market_id)
        shadow_evaluation = self.repository.get_latest_shadow_engine_evaluation_for_market(market_id)

        context_presence = {
            "snapshot": snapshot is not None,
            "weather_view": weather_view is not None,
            "outcome_resolution": outcome_resolution is not None,
            "calibration_sample": calibration_sample is not None,
            "shadow_evaluation": shadow_evaluation is not None,
        }
        complete_context = all(context_presence.values())
        gate_status = CommandGateStatus.ALLOW if complete_context else CommandGateStatus.WARN
        review_status_value = (
            CommandReviewStatus.READY
            if complete_context
            else CommandReviewStatus.PENDING
        )
        if review_status is not None:
            review_status_value = CommandReviewStatus(review_status) if not isinstance(review_status, CommandReviewStatus) else review_status

        if recommendation is not None:
            recommendation_value = (
                CommandReviewRecommendation(recommendation)
                if not isinstance(recommendation, CommandReviewRecommendation)
                else recommendation
            )
        else:
            recommendation_value = self._derive_recommendation(command_name, gate_status=gate_status)

        approval_status_value = (
            CommandApprovalStatus(approval_status)
            if approval_status is not None and not isinstance(approval_status, CommandApprovalStatus)
            else approval_status
        )
        if approval_status_value is None:
            approval_status_value = (
                CommandApprovalStatus.NOT_REQUIRED
                if gate_status == CommandGateStatus.ALLOW
                else CommandApprovalStatus.PENDING
            )

        command_review = CommandReviewRecord(
            command_review_id=f"crv_{uuid4().hex[:10]}",
            market_id=market_id,
            command_name=command_name,
            source_page=source_page,
            target_page=target_page,
            command_path=command_path,
            review_status=review_status_value,
            approval_status=approval_status_value,
            recommendation=recommendation_value,
            gate_status=gate_status,
            active_engine_id=(
                shadow_evaluation.get("primary_engine_id")
                if isinstance(shadow_evaluation, dict)
                else "gaussian_v0"
            ),
            execution_mode=self._current_execution_mode(),
            risk_status="SAFE" if gate_status == CommandGateStatus.ALLOW else "WARN",
            approval_window_valid=gate_status == CommandGateStatus.ALLOW,
            approval_valid_until=self._next_approval_window(),
            market_snapshot_archive_id=snapshot.get("snapshot_archive_id") if isinstance(snapshot, dict) else None,
            weather_view_archive_id=weather_view.get("weather_view_archive_id") if isinstance(weather_view, dict) else None,
            weather_forecast_archive_id=weather_forecast.get("forecast_archive_id") if isinstance(weather_forecast, dict) else None,
            probability_run_id=probability_run.get("run_id") if isinstance(probability_run, dict) else None,
            outcome_resolution_id=outcome_resolution.get("outcome_resolution_id") if isinstance(outcome_resolution, dict) else None,
            calibration_sample_id=calibration_sample.get("calibration_sample_id") if isinstance(calibration_sample, dict) else None,
            backtest_memory_id=backtest_memory.get("backtest_memory_id") if isinstance(backtest_memory, dict) else None,
            deb_shadow_run_id=deb_shadow_run.get("deb_shadow_run_id") if isinstance(deb_shadow_run, dict) else None,
            emos_shadow_run_id=emos_shadow_run.get("emos_shadow_run_id") if isinstance(emos_shadow_run, dict) else None,
            shadow_evaluation_id=shadow_evaluation.get("shadow_evaluation_id") if isinstance(shadow_evaluation, dict) else None,
            raw_payload=raw_payload or {
                "context_presence": context_presence,
                "command_name": command_name,
            },
            metadata=metadata or {},
        )
        self.repository.save_command_review_record(command_review)
        return command_review

    def build_all_eligible(self) -> list[CommandReviewRecord]:
        market_ids = self.repository.list_distinct_market_ids_for_calibration_memory()
        return [self.build_for_market(market_id) for market_id in market_ids]

    def list_reviews(
        self,
        limit: int = 100,
        market_id: str | None = None,
        review_status: str | None = None,
        approval_status: str | None = None,
        gate_status: str | None = None,
    ) -> list[dict]:
        return self.repository.list_command_review_records(
            limit=limit,
            market_id=market_id,
            review_status=review_status,
            approval_status=approval_status,
            gate_status=gate_status,
        )

    def get_market_bundle(self, market_id: str, limit: int = 100) -> CommandReviewBundle:
        return self.repository.get_command_review_bundle(market_id, limit=limit)

    def get_summary(self) -> CommandReviewSummary:
        return self.repository.get_command_review_summary()

    @staticmethod
    def _derive_recommendation(
        command_name: str,
        *,
        gate_status: CommandGateStatus,
    ) -> CommandReviewRecommendation:
        normalized = str(command_name or "").strip().lower()
        if normalized.startswith("/open") or "workstation" in normalized:
            return CommandReviewRecommendation.OPEN_WORKSTATION
        if normalized.startswith("/approve"):
            return CommandReviewRecommendation.REQUEST_APPROVAL
        if normalized.startswith("/block"):
            return CommandReviewRecommendation.BLOCK
        if normalized.startswith("/mute"):
            return CommandReviewRecommendation.MUTE_SIGNAL
        if gate_status == CommandGateStatus.ALLOW:
            return CommandReviewRecommendation.CREATE_PENDING_INTENT
        return CommandReviewRecommendation.REVIEW_EVIDENCE

    @staticmethod
    def _current_execution_mode() -> str:
        return "OBSERVE_ONLY"

    @staticmethod
    def _next_approval_window() -> str:
        from datetime import datetime, timedelta, timezone

        return (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
