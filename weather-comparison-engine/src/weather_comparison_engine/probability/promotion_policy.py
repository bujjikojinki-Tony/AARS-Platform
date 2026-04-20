from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from weather_comparison_engine.probability.contract_policy import ProbabilityContractPolicy
from weather_comparison_engine.settings import (
    PROBABILITY_CANDIDATE_MIN_RESOLVER_MATCH_RATE,
    PROBABILITY_LIVE_MIN_RESOLVER_MATCH_RATE,
)


PROMOTION_POLICY_VERSION = "promotion_policy.v1"


class PromotionPolicy:
    def __init__(self, *, now: datetime | None = None) -> None:
        self.now = now or datetime.now(timezone.utc)
        self.contract_policy = ProbabilityContractPolicy(now=self.now)

    def evaluate(
        self,
        *,
        probability_state: dict | None = None,
        validation_report: dict | None = None,
        validation_freshness_status: dict | None = None,
        label_coverage_report: dict | None = None,
        resolver_quality: dict | None = None,
    ) -> dict:
        state = probability_state if isinstance(probability_state, dict) else {}
        validation = validation_report if isinstance(validation_report, dict) else {}
        freshness = validation_freshness_status if isinstance(validation_freshness_status, dict) else {}
        coverage = label_coverage_report if isinstance(label_coverage_report, dict) else {}
        resolver = resolver_quality if isinstance(resolver_quality, dict) else {}

        base_source = state or validation
        base_contract = _base_probability_contract(base_source, validation_report=validation, policy=self.contract_policy)
        base_probability_mode = str(
            base_source.get("probability_mode")
            or base_contract.get("probability_mode")
            or "heuristic_not_calibrated"
        )
        base_execution_constraint = str(
            base_source.get("execution_constraint")
            or base_contract.get("execution_constraint")
            or "manual_advisory_only"
        )
        calibration_status = str(
            base_source.get("calibration_status")
            or base_contract.get("calibration_status")
            or "not_calibrated"
        )
        approved_for_live = bool(
            base_source.get("approved_for_live")
            if "approved_for_live" in base_source
            else base_contract.get("approved_for_live", False)
        )
        promotion_reason = str(
            base_source.get("promotion_reason")
            or base_contract.get("promotion_reason")
            or "thresholds_not_met"
        )
        validation_report_generated_at = (
            base_source.get("validation_report_generated_at")
            or base_contract.get("validation_report_generated_at")
        )

        freshness_status_raw = freshness.get("status") if freshness else validation.get("freshness_status")
        coverage_status_raw = coverage.get("status") if coverage else validation.get("coverage_status")
        freshness_known = freshness_status_raw not in (None, "")
        coverage_known = coverage_status_raw not in (None, "")
        freshness_status = str(freshness_status_raw or "unknown").lower()
        coverage_status = str(coverage_status_raw or "unknown").lower()
        resolver_match_rate = _resolver_match_rate(resolver, validation)
        source_match_grade = str(
            resolver.get("source_match_grade")
            or validation.get("source_match_grade")
            or base_source.get("source_match_grade")
            or ""
        ).lower()

        freshness_healthy = (not freshness_known) or freshness_status in {"healthy", "ok", "fresh"}
        coverage_healthy = (not coverage_known) or coverage_status in {"healthy", "ok"}
        precision_band = _resolver_precision_band(resolver_match_rate, source_match_grade)

        blockers: list[str] = []
        demotion_reason: str | None = None
        final_probability_mode = base_probability_mode
        final_execution_constraint = base_execution_constraint

        if freshness_known and not freshness_healthy:
            blockers.append(f"validation_freshness:{freshness_status}")
            demotion_reason = f"validation_freshness_{freshness_status}"
            final_probability_mode = "heuristic_not_calibrated"
            final_execution_constraint = "manual_advisory_only"
        elif coverage_known and not coverage_healthy:
            blockers.append(f"label_coverage:{coverage_status}")
            demotion_reason = f"label_coverage_{coverage_status}"
            if base_probability_mode == "live_approved" and precision_band in {"live", "candidate"}:
                final_probability_mode = "shadow_calibrated_candidate"
                final_execution_constraint = "dry_run_only"
            else:
                final_probability_mode = "heuristic_not_calibrated"
                final_execution_constraint = "manual_advisory_only"
        elif precision_band == "live":
            final_probability_mode = "live_approved"
            final_execution_constraint = "live_execution_allowed"
        elif precision_band == "candidate":
            if base_probability_mode == "live_approved":
                demotion_reason = "resolver_match_rate_low"
                blockers.append("resolver_precision_low")
                final_probability_mode = "shadow_calibrated_candidate"
                final_execution_constraint = "dry_run_only"
            else:
                final_probability_mode = "shadow_calibrated_candidate"
                final_execution_constraint = "dry_run_only"
        elif precision_band == "blocked":
            blockers.append("resolver_precision_low")
            demotion_reason = "resolver_precision_low"
            final_probability_mode = "heuristic_not_calibrated"
            final_execution_constraint = "manual_advisory_only"

        if final_probability_mode == "live_approved":
            approved_for_live = True
            if demotion_reason is None:
                promotion_reason = "live_thresholds_passed"
        elif final_probability_mode == "shadow_calibrated_candidate":
            approved_for_live = False
            if demotion_reason is None:
                promotion_reason = "candidate_thresholds_passed"
        else:
            approved_for_live = False
            if demotion_reason is not None:
                promotion_reason = demotion_reason
            else:
                promotion_reason = promotion_reason or "thresholds_not_met"

        return {
            "schema_version": "promotion_state.v1",
            "promotion_policy_version": PROMOTION_POLICY_VERSION,
            "generated_at": self.now.isoformat(),
            "base_probability_mode": base_probability_mode,
            "base_execution_constraint": base_execution_constraint,
            "probability_mode": final_probability_mode,
            "execution_constraint": final_execution_constraint,
            "calibration_status": calibration_status,
            "approved_for_live": approved_for_live,
            "promotion_reason": promotion_reason,
            "demotion_reason": demotion_reason,
            "blockers": blockers,
            "freshness_status": freshness_status if freshness_known else "-",
            "coverage_status": coverage_status if coverage_known else "-",
            "resolver_match_rate": resolver_match_rate,
            "source_match_grade": source_match_grade or "-",
            "contract_version": str(base_contract.get("contract_version") or "probability_contract.v1"),
            "probability_contract": base_contract,
            "validation_report_generated_at": validation_report_generated_at,
        }


def _base_probability_contract(
    base_source: dict,
    *,
    validation_report: dict | None,
    policy: ProbabilityContractPolicy,
) -> dict:
    existing = base_source.get("probability_contract")
    if isinstance(existing, dict) and existing:
        return existing
    if validation_report:
        evaluated = policy.evaluate(validation_report)
        contract = evaluated.get("probability_contract")
        return contract if isinstance(contract, dict) else {}
    return {}


def _resolver_match_rate(resolver: dict, validation: dict) -> float | None:
    for source in (
        resolver.get("resolver_match_rate"),
        validation.get("resolver_match_rate"),
        resolver.get("match_rate"),
        validation.get("match_rate"),
    ):
        if source is None:
            continue
        try:
            return float(source)
        except (TypeError, ValueError):
            continue
    return None


def _resolver_precision_band(resolver_match_rate: float | None, source_match_grade: str) -> str:
    if resolver_match_rate is None and source_match_grade in {"", "-", "unknown"}:
        return "unknown"
    if source_match_grade in {"exact_station", "exact", "matched"} and resolver_match_rate is None:
        return "live"
    if resolver_match_rate is None:
        return "blocked"
    if resolver_match_rate >= PROBABILITY_LIVE_MIN_RESOLVER_MATCH_RATE:
        return "live"
    if resolver_match_rate >= PROBABILITY_CANDIDATE_MIN_RESOLVER_MATCH_RATE:
        return "candidate"
    return "blocked"
