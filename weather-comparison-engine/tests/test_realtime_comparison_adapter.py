from weather_comparison_engine.compare.realtime_comparison_adapter import RealtimeComparisonAdapter


def test_realtime_comparison_adapter_marks_unmatched_rule():
    adapter = RealtimeComparisonAdapter()

    point = adapter.build_comparison_point(
        market_snapshot={
            "updated_at": "2026-04-13T00:00:00+00:00",
            "market_probability": 0.62,
            "favored_side": "yes",
            "yes_price": 0.62,
            "no_price": 0.38,
        },
        forecast_snapshot={
            "timestamp": "2026-04-13T00:01:00+00:00",
            "market_id": "693874",
            "rule_status": "no_matching_rule",
            "rule_market_id": None,
            "market_family": "sea_ice_extent",
            "resolution_scope": "global_index",
            "supported_by_current_pipeline": False,
            "band_scheme": "sea_ice_range_3way",
        },
        market_id="693874",
        market_band="26_or_below",
        confidence_score=0.0,
    )

    assert point["comparison_status"] == "unmatched_rule"
    assert point["rule_status"] == "no_matching_rule"
    assert point["market_family"] == "sea_ice_extent"
    assert point["band_scheme"] == "sea_ice_range_3way"
    assert point["market_probability"] == 0.62
    assert point["favored_side"] == "yes"


def test_realtime_comparison_adapter_accepts_matched_snapshot():
    adapter = RealtimeComparisonAdapter()

    point = adapter.build_comparison_point(
        market_snapshot={
            "updated_at": "2026-04-17T00:00:00+00:00",
            "market_probability": 0.58,
            "favored_side": "yes",
            "yes_price": 0.58,
            "no_price": 0.42,
            "market_band_scheme": "sea_ice_range_3way",
        },
        forecast_snapshot={
            "timestamp": "2026-04-17T00:01:00+00:00",
            "market_id": "693870",
            "rule_status": "matched_snapshot",
            "rule_market_id": "693870",
            "market_family": "sea_ice_extent",
            "resolution_scope": "global_index",
            "supported_by_current_pipeline": True,
            "required_data_source": "nsidc_arctic_sea_ice_extent",
            "band_scheme": "sea_ice_range_3way",
            "model_band": "in_range",
            "value": 4.1,
        },
        market_id="693870",
        market_band="in_range",
        confidence_score=0.95,
    )

    assert point["comparison_status"] == "aligned"
    assert point["rule_status"] == "matched_snapshot"
    assert point["band_scheme"] == "sea_ice_range_3way"
    assert point["confidence_adjusted_gap"] == 0.0
