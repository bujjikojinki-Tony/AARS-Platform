from __future__ import annotations

from weather_comparison_engine.probability import ShadowProbabilityEngine


def test_shadow_probability_engine_builds_positive_support_when_bands_match():
    engine = ShadowProbabilityEngine()
    state = engine.build_probability_state(
        market_snapshot={
            "market_id": "m1",
            "market_probability": 0.63,
            "market_band": "top_3",
        },
        forecast_snapshot={
            "market_id": "m1",
            "model_band": "top_3",
            "confidence_score": 0.9,
        },
        resolver_rule={
            "market_id": "m1",
            "resolver_status": "matched",
            "resolver_confidence": 0.8,
            "market_family": "global_temperature_index",
            "expected_band": "top_3",
            "band_scheme": "global_temperature_index_ordinal",
        },
    )

    assert state.mode == "shadow"
    assert state.calibration_status == "not_calibrated"
    assert state.probability_mode == "heuristic_not_calibrated"
    assert state.execution_constraint == "manual_advisory_only"
    assert state.approved_for_live is False
    assert state.deployment_mode == "shadow"
    assert state.model_probability == 0.72
    assert state.edge == 0.09
    assert state.confidence == 0.72


def test_shadow_probability_engine_blocks_unmatched_resolver():
    engine = ShadowProbabilityEngine()
    state = engine.build_probability_state(
        market_snapshot={
            "market_id": "m1",
            "market_probability": 0.63,
            "market_band": "in_range",
        },
        forecast_snapshot=None,
        resolver_rule={
            "market_id": "m1",
            "resolver_status": "unmatched",
            "resolver_reason": "missing_adapter",
        },
    )

    assert state.model_probability is None
    assert state.fair_value is None
    assert state.probability_mode == "heuristic_not_calibrated"
    assert state.probability_reason == "resolver_status=unmatched"


def test_shadow_probability_engine_penalizes_ordinal_distance():
    engine = ShadowProbabilityEngine()
    state = engine.build_probability_state(
        market_snapshot={
            "market_id": "m1",
            "market_probability": 0.67,
            "market_band": "top_3",
        },
        forecast_snapshot={
            "market_id": "m1",
            "model_band": "top_3",
            "confidence_score": 1.0,
        },
        resolver_rule={
            "market_id": "m1",
            "resolver_status": "matched",
            "resolver_confidence": 0.85,
            "expected_band": "top_1",
        },
    )

    assert state.model_probability == 0.4
    assert state.edge == -0.27
    assert state.probability_reason == "ordinal_band_distance=2"
