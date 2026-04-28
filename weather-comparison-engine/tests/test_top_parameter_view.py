from __future__ import annotations

from weather_comparison_engine.status.top_parameter_view import build_top_parameter_view


def test_build_top_parameter_view_surfaces_comparison_contract() -> None:
    view = build_top_parameter_view(
        current_market={
            "market_id": "m1",
            "market_family": "temperature_daily_max",
            "market_question": "Will Shanghai exceed 35C?",
            "location_name": "Shanghai",
            "target_date": "2026-04-20",
            "variable_name": "daily_max_temperature",
            "market_probability": 0.62,
            "yes_price": 0.64,
            "no_price": 0.36,
            "favored_side": "yes",
            "market_band": "35",
            "settlement_source_type": "station_observation",
            "official_vs_proxy_source": "official",
            "source_match_grade": "exact_station",
            "required_sources": ["metar", "wunderground"],
            "official_source_url": "https://example.com",
            "freshness_status": "healthy",
        },
        forecast_snapshot={
            "forecast_value": 34.8,
            "model_band": "35",
            "station_name": "Shanghai Pudong Intl Airport Station",
            "station_id": "ZSPD",
            "observed_at": "2026-04-19T09:30:00Z",
            "forecast_timestamp": "2026-04-19T10:00:00Z",
        },
        comparison_point={
            "fair_value": 0.71,
            "confidence_adjusted_edge": 0.08,
            "probability_mode": "shadow_calibrated_candidate",
            "execution_constraint": "dry_run_only",
            "can_execute": False,
            "primary_block_reason": "shadow_only",
            "recommended_operator_action": "refresh_pipeline_inputs",
            "comparison_status": "aligned",
        },
    )

    assert view["schema_version"] == "top_parameter_view.v2"
    assert view["market_id"] == "m1"
    assert view["polymarket"]["favored_side"] == "yes"
    assert view["weather"]["station_id"] == "ZSPD"
    assert view["weather"]["forecast_display_value"] == 34.8
    assert view["weather"]["forecast_canonical_value"] == 34.8
    assert view["weather"]["normalization_version"] == "measurement_normalization.v1"
    assert view["source_contract"]["source_match_grade"] == "exact_station"
    assert view["decision"]["primary_block_reason"] == "shadow_only"
    assert view["decision"]["can_execute"] == "no"


def test_build_top_parameter_view_derives_probability_without_probability_section() -> None:
    view = build_top_parameter_view(
        current_market={
            "market_id": "m2",
            "market_family": "sea_ice_extent",
            "market_question": "Will sea ice extent stay above threshold?",
            "location_name": "Arctic",
            "target_date": "2026-04-20",
            "variable_name": "sea_ice_extent",
            "yes_price": 0.35,
            "no_price": 0.65,
            "favored_side": "no",
            "market_band": "above",
        },
        forecast_snapshot={},
        comparison_point={
            "fair_value": 0.31,
            "confidence_adjusted_gap": 0.04,
            "probability_mode": "heuristic_not_calibrated",
            "execution_constraint": "manual_advisory_only",
            "can_execute": False,
            "primary_block_reason": "comparison_not_actionable",
            "comparison_status": "unknown",
        },
    )

    assert view["market_id"] == "m2"
    assert view["polymarket"]["market_implied_probability"] == 0.35
    assert view["weather"]["unit"] == "source_defined"
    assert view["normalization"]["canonical_unit"] == "source_defined"
