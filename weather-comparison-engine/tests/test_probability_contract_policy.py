from datetime import datetime, timedelta, timezone

from weather_comparison_engine.probability.contract_policy import ProbabilityContractPolicy


def test_probability_contract_policy_returns_heuristic_when_report_missing() -> None:
    policy = ProbabilityContractPolicy(now=datetime(2026, 4, 18, 8, 0, tzinfo=timezone.utc))

    contract = policy.evaluate(None)

    assert contract["probability_mode"] == "heuristic_not_calibrated"
    assert contract["execution_constraint"] == "manual_advisory_only"
    assert contract["promotion_reason"] == "validation_report_missing"


def test_probability_contract_policy_promotes_candidate_when_candidate_thresholds_pass() -> None:
    now = datetime(2026, 4, 18, 8, 0, tzinfo=timezone.utc)
    policy = ProbabilityContractPolicy(now=now)

    contract = policy.evaluate(
        {
            "generated_at": (now - timedelta(minutes=10)).isoformat(),
            "sample_count": 80,
            "labeled_sample_count": 40,
            "validation_metrics": {
                "brier_score": 0.22,
                "market_baseline_brier_score": 0.25,
                "calibration_error": 0.12,
                "roi_backtest": -0.01,
            },
            "resolver_quality": {
                "resolver_match_rate": 0.74,
            },
        }
    )

    assert contract["probability_mode"] == "shadow_calibrated_candidate"
    assert contract["execution_constraint"] == "dry_run_only"
    assert contract["calibration_status"] == "candidate"
    assert contract["approved_for_live"] is False


def test_probability_contract_policy_promotes_live_when_live_thresholds_pass() -> None:
    now = datetime(2026, 4, 18, 8, 0, tzinfo=timezone.utc)
    policy = ProbabilityContractPolicy(now=now)

    contract = policy.evaluate(
        {
            "generated_at": (now - timedelta(minutes=10)).isoformat(),
            "sample_count": 420,
            "labeled_sample_count": 280,
            "validation_metrics": {
                "brier_score": 0.14,
                "market_baseline_brier_score": 0.18,
                "calibration_error": 0.05,
                "roi_backtest": 0.09,
            },
            "resolver_quality": {
                "resolver_match_rate": 0.96,
            },
        }
    )

    assert contract["probability_mode"] == "live_approved"
    assert contract["execution_constraint"] == "live_execution_allowed"
    assert contract["approved_for_live"] is True
    assert contract["deployment_mode"] == "live"
