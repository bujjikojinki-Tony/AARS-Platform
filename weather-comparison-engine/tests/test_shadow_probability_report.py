from pathlib import Path

from weather_comparison_engine.probability.shadow_probability_report import (
    build_probability_shadow_report,
    write_probability_shadow_report,
    write_probability_state,
)
from weather_comparison_engine.schemas.probability_state import ProbabilityState


def test_probability_shadow_report_counts_and_ranks_edges(tmp_path: Path):
    active = ProbabilityState(
        market_id="m1",
        timestamp="2026-04-17T00:00:00+00:00",
        market_family="global_temperature_index",
        market_implied_probability=0.67,
        model_probability=0.4,
        fair_value=0.4,
        edge=-0.27,
        confidence_adjusted_edge=-0.2,
        probability_reason="ordinal_band_distance=2",
    )
    blocked = ProbabilityState(
        market_id="m2",
        timestamp="2026-04-17T00:00:00+00:00",
        market_family="sea_ice_extent",
        probability_reason="resolver_status=unmatched",
    )

    active_path = write_probability_state(active, tmp_path)
    blocked_path = write_probability_state(blocked, tmp_path)
    report = build_probability_shadow_report(
        [active, blocked],
        [active_path, blocked_path],
        contract={
            "calibration_status": "candidate",
            "probability_mode": "shadow_calibrated_candidate",
            "execution_constraint": "dry_run_only",
            "approved_for_live": False,
            "deployment_mode": "shadow",
            "promotion_reason": "candidate_thresholds_passed",
        },
    )

    assert report["tracked_markets"] == 2
    assert report["probability_mode"] == "shadow_calibrated_candidate"
    assert report["execution_constraint"] == "dry_run_only"
    assert report["calibration_status"] == "candidate"
    assert report["active_states"] == 1
    assert report["blocked_states"] == 1
    assert report["blocked_reason_counts"] == {"resolver_status=unmatched": 1}
    assert report["market_family_counts"]["global_temperature_index"] == 1
    assert report["top_edges"][0]["market_id"] == "m1"

    report_path = write_probability_shadow_report(
        report,
        tmp_path / "probability_shadow_report.json",
    )
    assert report_path.exists()
