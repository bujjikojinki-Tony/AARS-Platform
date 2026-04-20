from datetime import datetime, timezone

from weather_comparison_engine.schemas.training_sample import TrainingSample
from weather_comparison_engine.validation import ValidationQualityReportBuilder


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
