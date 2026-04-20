from datetime import datetime, timezone

from weather_comparison_engine.probability.promotion_policy import PromotionPolicy


def test_promotion_policy_demotes_live_when_label_coverage_is_blocked() -> None:
    policy = PromotionPolicy(now=datetime(2026, 4, 18, 8, 0, tzinfo=timezone.utc))

    payload = policy.evaluate(
        probability_state={
            "probability_mode": "live_approved",
            "execution_constraint": "live_execution_allowed",
            "calibration_status": "calibrated",
            "approved_for_live": True,
            "promotion_reason": "live_thresholds_passed",
            "probability_contract": {
                "contract_version": "probability_contract.v1",
                "probability_mode": "live_approved",
                "execution_constraint": "live_execution_allowed",
                "calibration_status": "calibrated",
            },
        },
        validation_report={
            "resolver_quality": {"resolver_match_rate": 0.95, "source_match_grade": "exact_station"},
        },
        validation_freshness_status={"status": "healthy"},
        label_coverage_report={"status": "blocked"},
        resolver_quality={"resolver_match_rate": 0.95, "source_match_grade": "exact_station"},
    )

    assert payload["probability_mode"] == "shadow_calibrated_candidate"
    assert payload["execution_constraint"] == "dry_run_only"
    assert payload["approved_for_live"] is False
    assert payload["demotion_reason"] == "label_coverage_blocked"
    assert "label_coverage:blocked" in payload["blockers"]


def test_promotion_policy_keeps_validation_only_reports_unchanged_without_extra_signals() -> None:
    policy = PromotionPolicy(now=datetime(2026, 4, 18, 8, 0, tzinfo=timezone.utc))

    payload = policy.evaluate(
        validation_report={
            "probability_mode": "shadow_calibrated_candidate",
            "execution_constraint": "dry_run_only",
            "calibration_status": "candidate",
            "approved_for_live": False,
            "promotion_reason": "candidate_thresholds_passed",
            "probability_contract": {
                "contract_version": "probability_contract.v1",
                "probability_mode": "shadow_calibrated_candidate",
                "execution_constraint": "dry_run_only",
                "calibration_status": "candidate",
            },
            "resolver_quality": {"resolver_match_rate": 0.74},
        }
    )

    assert payload["probability_mode"] == "shadow_calibrated_candidate"
    assert payload["execution_constraint"] == "dry_run_only"
    assert payload["demotion_reason"] is None
