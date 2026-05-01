from __future__ import annotations

from uuid import uuid4

from backend.models.deb_shadow import DebShadowDiagnosticRecord
from backend.models.deb_shadow import DebShadowMarketBundle
from backend.models.deb_shadow import DebShadowRunRecord
from backend.models.deb_shadow import DebShadowRunStatus
from backend.models.deb_shadow import DebShadowSummary


class DebShadowService:
    """Read-only DEB shadow computation over accepted calibration memory."""

    def __init__(self, repository):
        self.repository = repository

    def build_for_market(self, market_id: str) -> dict[str, object]:
        latest_sample = self._latest_sample_for_market(market_id)
        if not latest_sample:
            raise ValueError("latest calibration sample not found")

        eligible_samples = self.repository.list_calibration_samples(
            limit=1000,
            engine_id=latest_sample.get("engine_id"),
            sample_eligibility="ELIGIBLE",
            sample_status="READY",
        )
        if not eligible_samples:
            raise ValueError("no ELIGIBLE calibration samples available for DEB shadow build")

        base_probability = self._as_float(latest_sample.get("model_probability"))
        sample_count = len(eligible_samples)
        avg_probability_error = self._average(
            [
                self._as_float(item.get("actual_outcome_value")) - self._as_float(item.get("model_probability"))
                for item in eligible_samples
            ]
        )
        avg_model_brier = self._average(
            [self._as_float(item.get("model_brier_score")) for item in eligible_samples]
        )
        avg_market_brier = self._average(
            [self._as_float(item.get("market_brier_score")) for item in eligible_samples]
        )
        avg_model_edge = self._average(
            [
                self._as_float(item.get("model_probability")) - self._as_float(item.get("market_probability"))
                for item in eligible_samples
            ]
        )

        adjustment_weight = min(1.0, sample_count / 20.0)
        bias_adjustment = avg_probability_error * 0.5 * adjustment_weight
        deb_probability = self._clamp(base_probability + bias_adjustment)
        calibration_gap = avg_market_brier - avg_model_brier

        warnings: list[str] = []
        if sample_count < 5:
            warnings.append("DEB shadow built from a thin eligible sample set.")
        warnings.append("DEB shadow is shadow-only and does not change the active engine.")

        run = DebShadowRunRecord(
            deb_shadow_run_id=f"dsr_{uuid4().hex[:12]}",
            market_id=market_id,
            calibration_sample_id=latest_sample.get("calibration_sample_id"),
            engine_id="deb_shadow_v1",
            base_probability=base_probability,
            deb_probability=deb_probability,
            bias_adjustment=bias_adjustment,
            calibration_gap=calibration_gap,
            sample_count=sample_count,
            run_status=DebShadowRunStatus.READY,
            warnings=warnings,
            raw_payload={
                "latest_sample": latest_sample,
                "eligible_sample_ids": [item.get("calibration_sample_id") for item in eligible_samples],
            },
            metadata={"service": "DebShadowService"},
        )
        diagnostic = DebShadowDiagnosticRecord(
            deb_shadow_diagnostic_id=f"dsd_{uuid4().hex[:12]}",
            deb_shadow_run_id=run.deb_shadow_run_id,
            market_id=market_id,
            calibration_sample_id=latest_sample.get("calibration_sample_id"),
            sample_count=sample_count,
            avg_model_brier_score=avg_model_brier,
            avg_market_brier_score=avg_market_brier,
            avg_model_edge=avg_model_edge,
            avg_probability_error=avg_probability_error,
            adjustment_weight=adjustment_weight,
            notes="Real DEB shadow diagnostic from accepted calibration memory.",
            raw_payload={"latest_sample": latest_sample},
            metadata={"service": "DebShadowService"},
        )
        self.repository.save_deb_shadow_run(run)
        self.repository.save_deb_shadow_diagnostic(diagnostic)
        return {"run": run, "diagnostic": diagnostic}

    def build_all_eligible(self) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        for market_id in self.repository.list_distinct_market_ids_for_calibration_memory():
            latest_sample = self._latest_sample_for_market(market_id)
            if not latest_sample:
                continue
            if latest_sample.get("sample_eligibility") != "ELIGIBLE":
                continue
            if latest_sample.get("sample_status") != "READY":
                continue
            results.append(self.build_for_market(market_id))
        return results

    def list_runs(
        self,
        limit: int = 100,
        market_id: str | None = None,
        run_status: str | DebShadowRunStatus | None = None,
    ) -> list[dict]:
        return self.repository.list_deb_shadow_runs(
            limit=limit,
            market_id=market_id,
            run_status=run_status,
        )

    def list_diagnostics(
        self,
        limit: int = 100,
        market_id: str | None = None,
        deb_shadow_run_id: str | None = None,
    ) -> list[dict]:
        return self.repository.list_deb_shadow_diagnostics(
            limit=limit,
            market_id=market_id,
            deb_shadow_run_id=deb_shadow_run_id,
        )

    def get_market_bundle(self, market_id: str, limit: int = 100) -> DebShadowMarketBundle:
        return self.repository.get_deb_shadow_market_bundle(market_id, limit=limit)

    def get_summary(self) -> DebShadowSummary:
        return self.repository.get_deb_shadow_summary()

    def _latest_sample_for_market(self, market_id: str) -> dict | None:
        rows = self.repository.list_calibration_samples(market_id=market_id, limit=1)
        return rows[0] if rows else None

    def _average(self, values: list[float]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))

    def _as_float(self, value: object) -> float:
        if value is None:
            raise ValueError("required numeric DEB input is missing")
        return float(value)
