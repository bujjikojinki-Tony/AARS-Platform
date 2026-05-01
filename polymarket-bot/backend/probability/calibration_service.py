from __future__ import annotations

from uuid import uuid4

from backend.models.probability_governance import CalibrationResult
from backend.models.probability_governance import OutcomeStatus
from backend.probability.calibration_metrics import absolute_error
from backend.probability.calibration_metrics import brier_score
from backend.probability.calibration_metrics import probability_bucket


class CalibrationService:
    def __init__(self, repository):
        self.repository = repository

    def calibrate_market(self, market_id: str) -> list[CalibrationResult]:
        outcome = self.repository.get_latest_market_outcome(market_id)
        if not outcome:
            raise ValueError("market outcome not found")
        if outcome.get("status") != OutcomeStatus.RESOLVED.value:
            raise ValueError("market outcome is not RESOLVED")
        if outcome.get("resolved_direction_hit") is None:
            raise ValueError("resolved_direction_hit is required for calibration")

        actual_outcome = 1 if outcome["resolved_direction_hit"] else 0
        runs = self.repository.list_probability_engine_runs_for_market(market_id)
        if not runs:
            raise ValueError("no probability engine runs found for market")

        results: list[CalibrationResult] = []
        for run in runs:
            predicted = float(run["model_probability"])
            result = CalibrationResult(
                calibration_id=f"cal_{uuid4().hex[:10]}",
                market_id=market_id,
                engine_id=run["engine_id"],
                run_id=run["run_id"],
                outcome_id=outcome["outcome_id"],
                predicted_probability=predicted,
                actual_outcome=actual_outcome,
                brier_score=brier_score(predicted, actual_outcome),
                absolute_error=absolute_error(predicted, actual_outcome),
                bucket=probability_bucket(predicted),
            )
            self.repository.save_calibration_result(result)
            results.append(result)
        return results
