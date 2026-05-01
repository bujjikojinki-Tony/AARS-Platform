from __future__ import annotations

from uuid import uuid4

from backend.models.calibration_memory import BacktestMemoryRecord
from backend.models.calibration_memory import BacktestMemoryStatus
from backend.models.calibration_memory import CalibrationSample
from backend.models.calibration_memory import HypotheticalAction
from backend.models.calibration_memory import HypotheticalResult
from backend.models.calibration_memory import ResolvedOutcomeForMemory
from backend.models.calibration_memory import SampleEligibility


class BacktestMemoryBuilder:
    """Builds hypothetical read-only backtest memory from calibration samples only."""

    def __init__(self, repository, edge_threshold: float = 0.05):
        self.repository = repository
        self.edge_threshold = edge_threshold

    def build_from_sample(
        self,
        sample: CalibrationSample | dict,
        *,
        edge_threshold: float | None = None,
    ) -> BacktestMemoryRecord:
        item = sample if isinstance(sample, CalibrationSample) else CalibrationSample(**sample)
        threshold = self.edge_threshold if edge_threshold is None else float(edge_threshold)
        market_probability = self._as_float(item.market_probability)
        model_probability = self._as_float(item.model_probability)
        actual_outcome_value = self._as_float(item.actual_outcome_value)
        edge = model_probability - market_probability

        if edge >= threshold:
            action = HypotheticalAction.TAKE_YES
        elif edge <= -threshold:
            action = HypotheticalAction.TAKE_NO
        else:
            action = HypotheticalAction.SKIP

        outcome = item.resolved_outcome
        if action == HypotheticalAction.SKIP:
            result = HypotheticalResult.PUSH
        elif action == HypotheticalAction.TAKE_YES and outcome == ResolvedOutcomeForMemory.YES:
            result = HypotheticalResult.WIN
        elif action == HypotheticalAction.TAKE_YES and outcome == ResolvedOutcomeForMemory.NO:
            result = HypotheticalResult.LOSS
        elif action == HypotheticalAction.TAKE_NO and outcome == ResolvedOutcomeForMemory.NO:
            result = HypotheticalResult.WIN
        elif action == HypotheticalAction.TAKE_NO and outcome == ResolvedOutcomeForMemory.YES:
            result = HypotheticalResult.LOSS
        else:
            result = HypotheticalResult.PUSH

        record = BacktestMemoryRecord(
            backtest_memory_id=f"bm_{uuid4().hex[:12]}",
            market_id=item.market_id,
            snapshot_archive_id=item.snapshot_archive_id,
            weather_view_archive_id=item.weather_view_archive_id,
            weather_forecast_archive_id=item.weather_forecast_archive_id,
            probability_run_id=item.probability_run_id,
            outcome_resolution_id=item.outcome_resolution_id,
            engine_id=item.engine_id,
            market_probability=market_probability,
            model_probability=model_probability,
            actual_outcome_value=actual_outcome_value,
            edge=edge,
            edge_threshold=threshold,
            hypothetical_action=action,
            hypothetical_result=result,
            sample_eligibility=SampleEligibility.ELIGIBLE
            if item.sample_eligibility == SampleEligibility.ELIGIBLE
            else SampleEligibility(item.sample_eligibility),
            backtest_status=BacktestMemoryStatus.READY,
            raw_payload={"calibration_sample": item.model_dump(mode="json")},
            metadata={"builder": "BacktestMemoryBuilder"},
        )
        self.repository.save_backtest_memory_record(record)
        return record

    def _as_float(self, value: float | None) -> float:
        if value is None:
            raise ValueError("required numeric component is missing")
        return float(value)
