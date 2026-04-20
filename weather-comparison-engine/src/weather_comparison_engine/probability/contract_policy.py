from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from weather_comparison_engine.settings import (
    MODEL_VALIDATION_REFRESH_INTERVAL_SECONDS,
    PROBABILITY_CANDIDATE_MAX_CALIBRATION_ERROR,
    PROBABILITY_CANDIDATE_MIN_LABELED_SAMPLES,
    PROBABILITY_CANDIDATE_MIN_RESOLVER_MATCH_RATE,
    PROBABILITY_LIVE_MAX_BRIER_SCORE,
    PROBABILITY_LIVE_MAX_CALIBRATION_ERROR,
    PROBABILITY_LIVE_MIN_BACKTEST_ROI,
    PROBABILITY_LIVE_MIN_LABELED_SAMPLES,
    PROBABILITY_LIVE_MIN_RESOLVER_MATCH_RATE,
)
from weather_comparison_engine.schemas.probability_contract import build_probability_contract


class ProbabilityContractPolicy:
    def __init__(
        self,
        *,
        now: datetime | None = None,
        validation_stale_after_seconds: int | None = None,
    ) -> None:
        self.now = now or datetime.now(timezone.utc)
        self.validation_stale_after_seconds = (
            validation_stale_after_seconds
            if validation_stale_after_seconds is not None
            else max(MODEL_VALIDATION_REFRESH_INTERVAL_SECONDS * 3, 3600)
        )

    def evaluate(self, validation_report: dict | None) -> dict:
        if not validation_report:
            return _heuristic_contract("validation_report_missing", {})

        generated_at = _parse_iso(validation_report.get("generated_at"))
        if generated_at is None:
            return _heuristic_contract("validation_report_missing_generated_at", {})

        freshness_seconds = max((self.now - generated_at).total_seconds(), 0.0)
        metrics = validation_report.get("validation_metrics") or {}
        resolver_quality = validation_report.get("resolver_quality") or {}
        sample_count = int(validation_report.get("sample_count") or 0)
        labeled_sample_count = int(validation_report.get("labeled_sample_count") or 0)
        calibration_status = str(validation_report.get("calibration_status") or "not_calibrated")
        brier_score = _to_float(metrics.get("brier_score"))
        baseline_brier = _to_float(metrics.get("market_baseline_brier_score"))
        calibration_error = _to_float(metrics.get("calibration_error"))
        roi_backtest = _to_float(metrics.get("roi_backtest"))
        resolver_match_rate = _to_float(resolver_quality.get("resolver_match_rate"))

        checks = {
            "freshness_seconds": freshness_seconds,
            "sample_count": sample_count,
            "labeled_sample_count": labeled_sample_count,
            "brier_score": brier_score,
            "market_baseline_brier_score": baseline_brier,
            "calibration_error": calibration_error,
            "roi_backtest": roi_backtest,
            "resolver_match_rate": resolver_match_rate,
            "validation_stale_after_seconds": self.validation_stale_after_seconds,
        }

        if freshness_seconds > float(self.validation_stale_after_seconds):
            return _heuristic_contract("validation_report_stale", checks)

        live_checks = [
            labeled_sample_count >= PROBABILITY_LIVE_MIN_LABELED_SAMPLES,
            calibration_error is not None and calibration_error <= PROBABILITY_LIVE_MAX_CALIBRATION_ERROR,
            brier_score is not None and brier_score <= PROBABILITY_LIVE_MAX_BRIER_SCORE,
            baseline_brier is not None and brier_score is not None and brier_score <= baseline_brier,
            roi_backtest is not None and roi_backtest >= PROBABILITY_LIVE_MIN_BACKTEST_ROI,
            resolver_match_rate is not None
            and resolver_match_rate >= PROBABILITY_LIVE_MIN_RESOLVER_MATCH_RATE,
        ]
        if all(live_checks):
            return _with_contract({
                "calibration_status": "calibrated",
                "probability_mode": "live_approved",
                "execution_constraint": "live_execution_allowed",
                "approved_for_live": True,
                "deployment_mode": "live",
                "promotion_reason": "live_thresholds_passed",
                "contract_source": "validation_policy_v1",
                "contract_checks": checks,
                "validation_report_generated_at": generated_at.isoformat(),
            })

        candidate_checks = [
            labeled_sample_count >= PROBABILITY_CANDIDATE_MIN_LABELED_SAMPLES,
            calibration_error is not None and calibration_error <= PROBABILITY_CANDIDATE_MAX_CALIBRATION_ERROR,
            resolver_match_rate is not None
            and resolver_match_rate >= PROBABILITY_CANDIDATE_MIN_RESOLVER_MATCH_RATE,
        ]
        if all(candidate_checks):
            return _with_contract({
                "calibration_status": "candidate",
                "probability_mode": "shadow_calibrated_candidate",
                "execution_constraint": "dry_run_only",
                "approved_for_live": False,
                "deployment_mode": "shadow",
                "promotion_reason": "candidate_thresholds_passed",
                "contract_source": "validation_policy_v1",
                "contract_checks": checks,
                "validation_report_generated_at": generated_at.isoformat(),
            })

        reason = calibration_status if calibration_status and calibration_status != "unknown" else "thresholds_not_met"
        return _heuristic_contract(reason, checks, generated_at=generated_at)


def _heuristic_contract(reason: str, checks: dict[str, Any], generated_at: datetime | None = None) -> dict:
    payload = {
        "calibration_status": "not_calibrated",
        "probability_mode": "heuristic_not_calibrated",
        "execution_constraint": "manual_advisory_only",
        "approved_for_live": False,
        "deployment_mode": "shadow",
        "promotion_reason": reason,
        "contract_source": "validation_policy_v1",
        "contract_checks": checks,
    }
    if generated_at is not None:
        payload["validation_report_generated_at"] = generated_at.isoformat()
    return _with_contract(payload)


def _with_contract(payload: dict[str, Any]) -> dict[str, Any]:
    payload["contract_version"] = "probability_contract.v1"
    payload["probability_contract"] = build_probability_contract(payload)
    return payload


def _parse_iso(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
