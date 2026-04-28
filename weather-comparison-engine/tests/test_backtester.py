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
            canonical_value=28.0,
            canonical_unit="celsius",
            source_policy_ref="source_policy_registry.v1",
            normalization_version="measurement_normalization.v1",
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
            canonical_value=27.0,
            canonical_unit="celsius",
            source_policy_ref="source_policy_registry.v1",
            normalization_version="measurement_normalization.v1",
        ),
        TrainingSample(
            market_id="m3",
            timestamp="2026-04-03T00:00:00Z",
            market_family="sea_ice_extent",
            model_probability=0.53,
            market_probability=0.5,
            outcome="YES",
            is_labeled=True,
            canonical_value=17.0,
            canonical_unit="source_defined",
            source_policy_ref="source_policy_registry.v1",
            normalization_version="measurement_normalization.v1",
        ),
        TrainingSample(
            market_id="m4",
            timestamp="2026-04-04T00:00:00Z",
            market_family="sea_ice_extent",
            model_probability=0.52,
            market_probability=0.51,
            outcome="NO",
            is_labeled=True,
            canonical_value=16.5,
            canonical_unit="source_defined",
            source_policy_ref="source_policy_registry.v1",
            normalization_version="measurement_normalization.v1",
        ),
    ]

    report = backtester.run(samples, edge_threshold=0.05)

    assert report["sample_count"] == 4
    assert report["trade_count"] == 2
    assert report["position_counts"]["YES"] == 1
    assert report["position_counts"]["NO"] == 1
    assert report["hit_rate"] == 1.0
    assert report["roi"] == 0.45
    assert report["governance_summary"]["sample_count"] == 4
    assert report["governance_summary"]["canonical_ratio"] == 1.0
    assert report["family_rollout_summary"]["family_count"] == 2
    assert report["family_rollout_summary"]["coverage_ratio"] == 1.0
    assert report["family_rollout_summary"]["top_family"] == "sea_ice_extent"
    assert report["family_rollout_trend_summary"]["sample_count"] == 4
    assert report["family_rollout_trend_summary"]["bucket_count"] == 3
    assert len(report["family_rollout_trend_summary"]["trend_windows"]) == 3
    assert report["family_rollout_watchlist"]["sample_count"] == 4
    assert report["family_rollout_watchlist"]["watchlist_count"] == 2


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
            canonical_value=28.0,
            canonical_unit="celsius",
            source_policy_ref="source_policy_registry.v1",
            normalization_version="measurement_normalization.v1",
        )
    ]

    report = backtester.run(samples, edge_threshold=0.1)
    assert report["trade_count"] == 0
    assert report["roi"] is None
    assert report["family_rollout_trend_summary"]["sample_count"] == 1
    assert report["family_rollout_watchlist"]["sample_count"] == 1
