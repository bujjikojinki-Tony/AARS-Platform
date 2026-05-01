from __future__ import annotations

from uuid import uuid4

from backend.models.calibration_memory import CalibrationSample
from backend.models.calibration_memory import CalibrationSampleStatus
from backend.models.calibration_memory import ResolvedOutcomeForMemory
from backend.models.calibration_memory import SampleEligibility


class CalibrationSampleBuilder:
    """Builds calibration samples from existing persisted records only."""

    REQUIRED_COMPONENTS = (
        "market_snapshot_archive",
        "weather_view_archive",
        "weather_forecast_archive",
        "probability_engine_run",
        "outcome_resolution",
    )

    def __init__(self, repository):
        self.repository = repository

    def check_eligibility(self, market_id: str) -> dict[str, object]:
        snapshot = self.repository.get_latest_market_snapshot_archive_for_market(market_id)
        weather_view = self.repository.get_latest_weather_view_archive_for_market(market_id)
        forecast = self.repository.get_latest_weather_forecast_archive_for_market(market_id)
        probability_run = self.repository.get_latest_probability_engine_run_for_market(market_id)
        resolution = self.repository.get_latest_outcome_resolution_for_market(market_id)

        components = {
            "market_snapshot_archive": snapshot,
            "weather_view_archive": weather_view,
            "weather_forecast_archive": forecast,
            "probability_engine_run": probability_run,
            "outcome_resolution": resolution,
        }
        missing = [name for name, value in components.items() if not value]
        eligibility = SampleEligibility.ELIGIBLE if not missing else SampleEligibility.PARTIAL
        actual_outcome = self._actual_outcome_value((resolution or {}).get("resolved_outcome"))
        if actual_outcome is None:
            eligibility = SampleEligibility.INELIGIBLE
        return {
            "market_id": market_id,
            "eligibility": eligibility.value,
            "missing_components": missing,
            "actual_outcome_value": actual_outcome,
            "available_components": {
                key: value is not None for key, value in components.items()
            },
        }

    def build_for_market(self, market_id: str) -> CalibrationSample:
        eligibility = self.check_eligibility(market_id)
        if eligibility["eligibility"] != SampleEligibility.ELIGIBLE.value:
            raise ValueError(
                f"market {market_id} is not ELIGIBLE for calibration sample build: "
                f"{', '.join(eligibility['missing_components']) or 'missing resolved outcome'}"
            )

        snapshot = self.repository.get_latest_market_snapshot_archive_for_market(market_id)
        weather_view = self.repository.get_latest_weather_view_archive_for_market(market_id)
        forecast = self.repository.get_latest_weather_forecast_archive_for_market(market_id)
        probability_run = self.repository.get_latest_probability_engine_run_for_market(market_id)
        resolution = self.repository.get_latest_outcome_resolution_for_market(market_id)

        assert snapshot is not None
        assert weather_view is not None
        assert forecast is not None
        assert probability_run is not None
        assert resolution is not None

        market_probability = self._as_float(snapshot.get("yes_price"))
        model_probability = self._as_float(probability_run.get("model_probability"))
        actual_outcome = self._actual_outcome_value(resolution.get("resolved_outcome"))
        if actual_outcome is None:
            raise ValueError("resolved outcome is not usable for calibration memory")

        model_brier = (model_probability - actual_outcome) ** 2
        market_brier = (market_probability - actual_outcome) ** 2
        model_abs_error = abs(model_probability - actual_outcome)
        market_abs_error = abs(market_probability - actual_outcome)

        sample = CalibrationSample(
            calibration_sample_id=f"cs_{uuid4().hex[:12]}",
            market_id=market_id,
            snapshot_archive_id=snapshot.get("snapshot_archive_id"),
            weather_view_archive_id=weather_view.get("weather_view_archive_id"),
            weather_forecast_archive_id=forecast.get("forecast_archive_id"),
            probability_run_id=probability_run.get("run_id"),
            outcome_resolution_id=resolution.get("outcome_resolution_id"),
            engine_id=probability_run.get("engine_id"),
            market_probability=market_probability,
            model_probability=model_probability,
            actual_outcome_value=actual_outcome,
            model_brier_score=model_brier,
            market_brier_score=market_brier,
            model_absolute_error=model_abs_error,
            market_absolute_error=market_abs_error,
            model_beats_market=model_brier < market_brier,
            resolved_outcome=self._resolved_outcome_for_memory(resolution.get("resolved_outcome")),
            sample_eligibility=SampleEligibility.ELIGIBLE,
            sample_status=CalibrationSampleStatus.READY,
            raw_payload={
                "market_snapshot_archive": snapshot,
                "weather_view_archive": weather_view,
                "weather_forecast_archive": forecast,
                "probability_engine_run": probability_run,
                "outcome_resolution": resolution,
            },
            metadata={"builder": "CalibrationSampleBuilder"},
        )
        self.repository.save_calibration_sample(sample)
        return sample

    def build_all_eligible(self) -> list[CalibrationSample]:
        items: list[CalibrationSample] = []
        for market_id in self.repository.list_distinct_market_ids_for_calibration_memory():
            if self.check_eligibility(market_id)["eligibility"] != SampleEligibility.ELIGIBLE.value:
                continue
            items.append(self.build_for_market(market_id))
        return items

    def _actual_outcome_value(self, value: object) -> float | None:
        if value == ResolvedOutcomeForMemory.YES.value:
            return 1.0
        if value == ResolvedOutcomeForMemory.NO.value:
            return 0.0
        return None

    def _resolved_outcome_for_memory(self, value: object) -> ResolvedOutcomeForMemory:
        if isinstance(value, ResolvedOutcomeForMemory):
            return value
        return ResolvedOutcomeForMemory(str(value or ResolvedOutcomeForMemory.UNKNOWN.value))

    def _as_float(self, value: object) -> float:
        if value is None:
            raise ValueError("required numeric component is missing")
        return float(value)
