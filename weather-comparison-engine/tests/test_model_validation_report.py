import json

from weather_comparison_engine.schemas.training_sample import TrainingSample
from weather_comparison_engine.validation import (
    build_model_validation_report,
    load_training_samples_jsonl,
)


def test_model_validation_report_builds_expected_sections():
    samples = [
        TrainingSample(
            market_id="m1",
            timestamp="2026-04-01T00:00:00Z",
            market_family="station_temperature",
            model_probability=0.8,
            market_probability=0.6,
            yes_price=0.6,
            outcome="YES",
            is_labeled=True,
        ),
        TrainingSample(
            market_id="m2",
            timestamp="2026-04-02T00:00:00Z",
            market_family="sea_ice_extent",
            model_probability=0.2,
            market_probability=0.4,
            no_price=0.6,
            outcome="NO",
            is_labeled=True,
        ),
    ]

    calibration_report, backtest_report, validation_report = build_model_validation_report(
        samples,
        calibration_bucket_count=5,
        edge_threshold=0.05,
    )

    assert calibration_report["model_probability"]["sample_count"] == 2
    assert backtest_report["trade_count"] == 2
    assert validation_report["deployment_mode"] == "shadow"
    assert validation_report["probability_mode"] == "heuristic_not_calibrated"
    assert validation_report["execution_constraint"] == "manual_advisory_only"
    assert validation_report["approved_for_live"] is False
    assert validation_report["promotion_state"]["probability_mode"] == "heuristic_not_calibrated"
    assert validation_report["promotion_state"]["promotion_policy_version"] == "promotion_policy.v1"
    assert validation_report["validation_metrics"]["brier_score"] is not None
    assert "station_temperature" in validation_report["family_validation"]
    assert validation_report["family_validation"]["station_temperature"]["sample_count"] == 1
    assert len(validation_report["edge_deciles"]) >= 1
    assert validation_report["resolver_quality"]["sample_count"] == 2


def test_load_training_samples_jsonl_reads_jsonl(tmp_path):
    path = tmp_path / "training_samples.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "market_id": "m1",
                        "timestamp": "2026-04-01T00:00:00Z",
                        "model_probability": 0.7,
                        "outcome": "YES",
                        "is_labeled": True,
                    }
                ),
                json.dumps(
                    {
                        "market_id": "m2",
                        "timestamp": "2026-04-02T00:00:00Z",
                        "model_probability": 0.3,
                        "outcome": "NO",
                        "is_labeled": True,
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    samples = load_training_samples_jsonl(path)
    assert len(samples) == 2
    assert samples[0].market_id == "m1"
