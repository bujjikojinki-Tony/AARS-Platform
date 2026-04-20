from weather_comparison_engine.compare.comparison_builder import ComparisonBuilder


def test_build_comparison_state():
    builder = ComparisonBuilder()

    signal = {
        "market_id": "sample_market_001",
        "location_name": "Central Park",
        "target_date": "2026-04-12",
        "variable_name": "daily_max_temperature",
        "model_band": "28",
        "market_band": "27",
        "confidence": {"score": 0.91},
        "action_hint": "approve_small",
    }
    market_bundle = {
        "market": {
            "market_id": "sample_market_001",
            "market_question": "Highest temperature in Central Park on Apr 12?",
        },
        "price_state": {
            "implied_band": "27",
        },
    }

    comparison = builder.build(signal=signal, market_bundle=market_bundle)

    assert comparison.market_id == "sample_market_001"
    assert comparison.model_band == "28"
    assert comparison.market_band == "27"
    assert comparison.divergence.band_distance == 1
