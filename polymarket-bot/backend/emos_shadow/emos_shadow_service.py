from __future__ import annotations

from math import sqrt
from uuid import uuid4

from backend.models.emos_shadow import EmosShadowDiagnosticRecord
from backend.models.emos_shadow import EmosShadowMarketBundle
from backend.models.emos_shadow import EmosShadowRunRecord
from backend.models.emos_shadow import EmosShadowRunStatus
from backend.models.emos_shadow import EmosShadowSummary


class EmosShadowService:
    """Read-only EMOS-style shadow computation over accepted calibration memory."""

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
            raise ValueError("no ELIGIBLE calibration samples available for EMOS shadow build")

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
        avg_absolute_error = self._average(
            [self._as_float(item.get("model_absolute_error")) for item in eligible_samples]
        )

        location_weight = min(1.0, sample_count / 25.0)
        scale_weight = min(0.5, avg_absolute_error)
        location_adjustment = avg_probability_error * 0.4 * location_weight
        spread_from_mid = abs(base_probability - 0.5)
        scale_direction = 1.0 if avg_probability_error >= 0 else -1.0
        scale_adjustment = spread_from_mid * 0.1 * scale_weight * scale_direction
        emos_probability = self._clamp(base_probability + location_adjustment + scale_adjustment)

        warnings: list[str] = []
        if sample_count < 5:
            warnings.append("EMOS shadow built from a thin eligible sample set.")
        warnings.append("EMOS shadow is shadow-only and does not change the active engine.")

        run = EmosShadowRunRecord(
            emos_shadow_run_id=f"esr_{uuid4().hex[:12]}",
            market_id=market_id,
            calibration_sample_id=latest_sample.get("calibration_sample_id"),
            engine_id="emos_shadow_v1",
            base_probability=base_probability,
            emos_probability=emos_probability,
            location_adjustment=location_adjustment,
            scale_adjustment=scale_adjustment,
            sample_count=sample_count,
            run_status=EmosShadowRunStatus.READY,
            warnings=warnings,
            raw_payload={
                "latest_sample": latest_sample,
                "eligible_sample_ids": [item.get("calibration_sample_id") for item in eligible_samples],
            },
            metadata={"service": "EmosShadowService"},
        )
        diagnostic = EmosShadowDiagnosticRecord(
            emos_shadow_diagnostic_id=f"esd_{uuid4().hex[:12]}",
            emos_shadow_run_id=run.emos_shadow_run_id,
            market_id=market_id,
            calibration_sample_id=latest_sample.get("calibration_sample_id"),
            sample_count=sample_count,
            avg_model_brier_score=avg_model_brier,
            avg_market_brier_score=avg_market_brier,
            avg_probability_error=avg_probability_error,
            avg_absolute_error=avg_absolute_error,
            location_weight=location_weight,
            scale_weight=scale_weight,
            notes="Real EMOS shadow diagnostic from accepted calibration memory.",
            raw_payload={
                "latest_sample": latest_sample,
                "std_like_error": sqrt(max(avg_model_brier, 0.0)),
            },
            metadata={"service": "EmosShadowService"},
        )
        self.repository.save_emos_shadow_run(run)
        self.repository.save_emos_shadow_diagnostic(diagnostic)
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
        run_status: str | EmosShadowRunStatus | None = None,
    ) -> list[dict]:
        return self.repository.list_emos_shadow_runs(
            limit=limit,
            market_id=market_id,
            run_status=run_status,
        )

    def list_diagnostics(
        self,
        limit: int = 100,
        market_id: str | None = None,
        emos_shadow_run_id: str | None = None,
    ) -> list[dict]:
        return self.repository.list_emos_shadow_diagnostics(
            limit=limit,
            market_id=market_id,
            emos_shadow_run_id=emos_shadow_run_id,
        )

    def get_market_bundle(self, market_id: str, limit: int = 100) -> EmosShadowMarketBundle:
        return self.repository.get_emos_shadow_market_bundle(market_id, limit=limit)

    def get_summary(self) -> EmosShadowSummary:
        return self.repository.get_emos_shadow_summary()

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
            raise ValueError("required numeric EMOS input is missing")
        return float(value)
