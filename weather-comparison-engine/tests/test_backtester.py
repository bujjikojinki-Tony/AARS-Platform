from weather_comparison_engine.schemas.training_sample import TrainingSample
from weather_comparison_engine.validation import Backtester


def test_backtester_runs_yes_and_no_trades():
    backtester = Backtester()
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
            market_family="station_temperature",
            model_probability=0.2,
            market_probability=0.5,
            no_price=0.5,
            outcome="NO",
            is_labeled=True,
        ),
        TrainingSample(
            market_id="m3",
            timestamp="2026-04-03T00:00:00Z",
            market_family="sea_ice_extent",
            model_probability=0.53,
            market_probability=0.5,
            outcome="YES",
            is_labeled=True,
        ),
    ]

    report = backtester.run(samples, edge_threshold=0.05)

    assert report["sample_count"] == 3
    assert report["trade_count"] == 2
    assert report["position_counts"]["YES"] == 1
    assert report["position_counts"]["NO"] == 1
    assert report["hit_rate"] == 1.0
    assert report["roi"] == 0.45


def test_backtester_handles_no_trades():
    backtester = Backtester()
    samples = [
        TrainingSample(
            market_id="m1",
            timestamp="2026-04-01T00:00:00Z",
            model_probability=0.51,
            market_probability=0.5,
            outcome="YES",
            is_labeled=True,
        )
    ]

    report = backtester.run(samples, edge_threshold=0.1)
    assert report["trade_count"] == 0
    assert report["roi"] is None
