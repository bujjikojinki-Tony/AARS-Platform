from weather_comparison_engine.schemas.training_sample import TrainingSample
from weather_comparison_engine.validation import CalibrationEvaluator


def test_calibration_evaluator_reports_metrics_and_curve():
    evaluator = CalibrationEvaluator()
    samples = [
        TrainingSample(market_id="m1", timestamp="2026-04-01T00:00:00Z", model_probability=0.9, outcome="YES", is_labeled=True),
        TrainingSample(market_id="m2", timestamp="2026-04-02T00:00:00Z", model_probability=0.8, outcome="YES", is_labeled=True),
        TrainingSample(market_id="m3", timestamp="2026-04-03T00:00:00Z", model_probability=0.2, outcome="NO", is_labeled=True),
        TrainingSample(market_id="m4", timestamp="2026-04-04T00:00:00Z", model_probability=0.1, outcome="NO", is_labeled=True),
    ]

    report = evaluator.evaluate(samples, probability_field="model_probability", bucket_count=5)

    assert report["sample_count"] == 4
    assert report["brier_score"] is not None
    assert report["log_loss"] is not None
    assert report["calibration_error"] is not None
    assert report["hit_rate"] == 1.0
    assert len(report["reliability_curve"]) >= 2


def test_calibration_evaluator_handles_empty_labeled_set():
    evaluator = CalibrationEvaluator()
    report = evaluator.evaluate(
        [TrainingSample(market_id="m1", timestamp="2026-04-01T00:00:00Z", model_probability=None)],
        probability_field="model_probability",
    )

    assert report["sample_count"] == 0
    assert report["brier_score"] is None
    assert report["reliability_curve"] == []
