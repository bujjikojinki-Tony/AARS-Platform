from datetime import datetime, timezone

from weather_comparison_engine.schemas.training_sample import TrainingSample
from weather_comparison_engine.validation import (
    ValidationQualityReportBuilder,
    build_validation_assimilation_summary,
)


def test_validation_freshness_status_blocks_when_validation_is_stale() -> None:
    builder = ValidationQualityReportBuilder(now=datetime(2026, 4, 18, 8, 0, tzinfo=timezone.utc))

    payload = builder.build_validation_freshness_status(
        {
            "generated_at": "2026-04-18T03:00:00+00:00",
            "probability_mode": "heuristic_not_calibrated",
            "execution_constraint": "manual_advisory_only",
        },
        warning_after_seconds=1800,
        stale_after_seconds=3600,
    )

    assert payload["status"] == "blocked"
    assert payload["reason"] == "validation_report_stale"


def test_label_coverage_report_blocks_when_labeled_rows_are_too_low() -> None:
    builder = ValidationQualityReportBuilder(now=datetime(2026, 4, 18, 8, 0, tzinfo=timezone.utc))
    samples = [
        TrainingSample(market_id="m1", timestamp="2026-04-18T00:00:00+00:00", market_family="station_temperature", is_labeled=True),
        TrainingSample(market_id="m2", timestamp="2026-04-18T00:01:00+00:00", market_family="station_temperature", is_labeled=False),
    ]

    payload = builder.build_label_coverage_report(
        samples,
        min_labeled_rows=3,
        min_labeled_ratio=0.6,
        min_family_labeled_rows=2,
    )

    assert payload["status"] == "blocked"
    assert "labeled_rows_below_min" in payload["blockers"]
    assert "labeled_ratio_below_min" in payload["blockers"]
    assert payload["market_family_coverage"]["station_temperature"]["status"] == "blocked"


def test_validation_assimilation_summary_reflects_governance_and_watchlist() -> None:
    samples = [
        TrainingSample(
            market_id="m1",
            timestamp="2026-04-18T00:00:00+00:00",
            market_family="station_temperature",
            is_labeled=True,
            canonical_value=28.0,
            canonical_unit="celsius",
            source_policy_ref="source_policy_registry.v1",
            normalization_version="measurement_normalization.v1",
        ),
        TrainingSample(
            market_id="m2",
            timestamp="2026-04-18T01:00:00+00:00",
            market_family="sea_ice_extent",
            is_labeled=True,
            canonical_value=17.0,
            canonical_unit="source_defined",
            source_policy_ref="source_policy_registry.v1",
            normalization_version="measurement_normalization.v1",
        ),
    ]

    summary = build_validation_assimilation_summary(
        samples,
        validation_report={
            "calibration_status": "heuristic_not_calibrated",
            "family_rollout_summary": {
                "family_count": 2,
                "ready_family_count": 1,
                "coverage_ratio": 1.0,
                "ready_ratio": 0.5,
                "top_family": "station_temperature",
                "top_drift_family": "sea_ice_extent",
                "top_drift_value": 0.04,
            },
            "family_rollout_trend_summary": {"drift_movement": 0.03},
            "family_rollout_watchlist": {
                "watchlist_count": 1,
                "stalled_family_count": 1,
                "drift_spike_family_count": 1,
                "expansion_backlog_count": 1,
                "top_watchlist_family": "sea_ice_extent",
                "top_watchlist_attention_level": "critical",
                "top_watchlist_reason": "drift_spike+drift=0.0875",
            },
            "governance_summary": {
                "canonical_ratio": 1.0,
                "source_policy_coverage": 1.0,
                "normalization_coverage": 1.0,
                "source_policy_sample_count": 2,
                "canonical_sample_count": 2,
            },
        },
        label_coverage_report={"status": "healthy", "labeled_ratio": 1.0},
        backtest_report={"trade_count": 2, "roi": 0.12},
    )

    assert summary["schema_version"] == "validation_assimilation_summary.v1"
    assert summary["feature_store_ready"] is True
    assert summary["label_store_ready"] is True
    assert summary["backtest_ready"] is True
    assert summary["assimilation_status"] == "blocked"
    assert summary["primary_blocker"] == "calibration:heuristic_not_calibrated"
    assert summary["top_watchlist_family"] == "sea_ice_extent"
