from weather_comparison_engine.schemas.training_sample import TrainingSample
from weather_comparison_engine.validation import build_family_rollout_watchlist


def test_family_rollout_watchlist_prioritizes_stalled_families():
    samples = [
        TrainingSample(
            market_id="m1",
            timestamp="2026-04-01T00:00:00Z",
            market_family="station_temperature",
            model_probability=0.8,
            market_probability=0.6,
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
            model_probability=0.7,
            market_probability=0.5,
            outcome="YES",
            is_labeled=True,
            canonical_value=29.0,
            canonical_unit="celsius",
            source_policy_ref="source_policy_registry.v1",
            normalization_version="measurement_normalization.v1",
        ),
        TrainingSample(
            market_id="m3",
            timestamp="2026-04-03T00:00:00Z",
            market_family="sea_ice_extent",
            model_probability=0.2,
            market_probability=0.4,
            outcome="NO",
            is_labeled=False,
            canonical_value=17.0,
            canonical_unit="source_defined",
            source_policy_ref="source_policy_registry.v1",
            normalization_version="measurement_normalization.v1",
        ),
        TrainingSample(
            market_id="m4",
            timestamp="2026-04-04T00:00:00Z",
            market_family="sea_ice_extent",
            model_probability=0.1,
            market_probability=0.5,
            outcome="NO",
            is_labeled=False,
            canonical_value=16.0,
            canonical_unit="source_defined",
            source_policy_ref="source_policy_registry.v1",
            normalization_version="measurement_normalization.v1",
        ),
    ]

    watchlist = build_family_rollout_watchlist(samples)

    assert watchlist["sample_count"] == 4
    assert watchlist["family_count"] == 2
    assert watchlist["watchlist_count"] == 2
    assert watchlist["stalled_family_count"] == 1
    assert watchlist["drift_spike_family_count"] == 2
    assert watchlist["expansion_backlog_count"] == 1
    assert watchlist["top_watchlist_family"] == "sea_ice_extent"
    assert watchlist["top_watchlist_attention_level"] == "critical"
    assert watchlist["watchlist"][0]["suggested_action"] == "prioritize_backfill_and_resolver_review"
