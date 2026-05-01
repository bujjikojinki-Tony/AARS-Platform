from __future__ import annotations

from uuid import uuid4

from backend.models.shadow_engine_evaluation import BestShadowEngine
from backend.models.shadow_engine_evaluation import ShadowEngineEvaluationBundle
from backend.models.shadow_engine_evaluation import ShadowEngineEvaluationRecord
from backend.models.shadow_engine_evaluation import ShadowEvaluationStatus
from backend.models.shadow_engine_evaluation import ShadowEngineEvaluationSummary


class ShadowEngineEvaluationService:
    """Read-only cross-engine historical comparison over accepted memory and shadow outputs."""

    def __init__(self, repository):
        self.repository = repository

    def build_for_market(self, market_id: str) -> ShadowEngineEvaluationRecord:
        sample = self._latest_sample_for_market(market_id)
        if not sample:
            raise ValueError("latest calibration sample not found")

        deb_run = self.repository.get_latest_deb_shadow_run_for_market(market_id)
        emos_run = self.repository.get_latest_emos_shadow_run_for_market(market_id)
        if not deb_run:
            raise ValueError("latest DEB shadow run not found")
        if not emos_run:
            raise ValueError("latest EMOS shadow run not found")

        primary_probability = self._as_float(sample.get("model_probability"))
        deb_probability = self._as_float(deb_run.get("deb_probability"))
        emos_probability = self._as_float(emos_run.get("emos_probability"))
        actual_outcome_value = self._as_float(sample.get("actual_outcome_value"))

        primary_brier = self._brier(primary_probability, actual_outcome_value)
        deb_brier = self._brier(deb_probability, actual_outcome_value)
        emos_brier = self._brier(emos_probability, actual_outcome_value)
        primary_abs = abs(primary_probability - actual_outcome_value)
        deb_abs = abs(deb_probability - actual_outcome_value)
        emos_abs = abs(emos_probability - actual_outcome_value)

        best_engine = self._best_engine(
            primary_brier=primary_brier,
            deb_brier=deb_brier,
            emos_brier=emos_brier,
        )

        record = ShadowEngineEvaluationRecord(
            shadow_evaluation_id=f"see_{uuid4().hex[:12]}",
            market_id=market_id,
            calibration_sample_id=sample.get("calibration_sample_id"),
            outcome_resolution_id=sample.get("outcome_resolution_id"),
            primary_engine_id=str(sample.get("engine_id") or "gaussian_v0"),
            deb_engine_id=str(deb_run.get("engine_id") or "deb_shadow_v1"),
            emos_engine_id=str(emos_run.get("engine_id") or "emos_shadow_v1"),
            primary_probability=primary_probability,
            deb_probability=deb_probability,
            emos_probability=emos_probability,
            actual_outcome_value=actual_outcome_value,
            primary_brier_score=primary_brier,
            deb_brier_score=deb_brier,
            emos_brier_score=emos_brier,
            primary_absolute_error=primary_abs,
            deb_absolute_error=deb_abs,
            emos_absolute_error=emos_abs,
            best_engine=best_engine,
            evaluation_status=ShadowEvaluationStatus.READY,
            raw_payload={
                "calibration_sample": sample,
                "deb_shadow_run": deb_run,
                "emos_shadow_run": emos_run,
            },
            metadata={"service": "ShadowEngineEvaluationService"},
        )
        self.repository.save_shadow_engine_evaluation(record)
        return record

    def build_all_eligible(self) -> list[ShadowEngineEvaluationRecord]:
        items: list[ShadowEngineEvaluationRecord] = []
        for market_id in self.repository.list_distinct_market_ids_for_calibration_memory():
            sample = self._latest_sample_for_market(market_id)
            if not sample:
                continue
            if sample.get("sample_eligibility") != "ELIGIBLE":
                continue
            if sample.get("sample_status") != "READY":
                continue
            if not self.repository.get_latest_deb_shadow_run_for_market(market_id):
                continue
            if not self.repository.get_latest_emos_shadow_run_for_market(market_id):
                continue
            items.append(self.build_for_market(market_id))
        return items

    def list_evaluations(
        self,
        limit: int = 100,
        market_id: str | None = None,
        evaluation_status: str | ShadowEvaluationStatus | None = None,
        best_engine: str | BestShadowEngine | None = None,
    ) -> list[dict]:
        return self.repository.list_shadow_engine_evaluations(
            limit=limit,
            market_id=market_id,
            evaluation_status=evaluation_status,
            best_engine=best_engine,
        )

    def get_market_bundle(self, market_id: str, limit: int = 100) -> ShadowEngineEvaluationBundle:
        return self.repository.get_shadow_engine_evaluation_bundle(market_id, limit=limit)

    def get_summary(self) -> ShadowEngineEvaluationSummary:
        return self.repository.get_shadow_engine_evaluation_summary()

    def _latest_sample_for_market(self, market_id: str) -> dict | None:
        rows = self.repository.list_calibration_samples(market_id=market_id, limit=1)
        return rows[0] if rows else None

    def _as_float(self, value: object) -> float:
        if value is None:
            raise ValueError("required numeric evaluation input is missing")
        return float(value)

    def _brier(self, probability: float, outcome: float) -> float:
        return (probability - outcome) ** 2

    def _best_engine(
        self,
        *,
        primary_brier: float,
        deb_brier: float,
        emos_brier: float,
    ) -> BestShadowEngine:
        scores = {
            BestShadowEngine.GAUSSIAN: primary_brier,
            BestShadowEngine.DEB_SHADOW: deb_brier,
            BestShadowEngine.EMOS_SHADOW: emos_brier,
        }
        best_score = min(scores.values())
        winners = [engine for engine, score in scores.items() if abs(score - best_score) < 1e-12]
        if len(winners) != 1:
            return BestShadowEngine.TIE
        return winners[0]
