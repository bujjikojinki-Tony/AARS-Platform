import pandas as pd

from weather_dashboard.ui.history_relationship_panel import build_history_relationship_summary


def test_build_history_relationship_summary_surfaces_top_parameter_view() -> None:
    history_df = pd.DataFrame(
        [
            {
                "timestamp": "2026-04-19T09:00:00Z",
                "market_id": "m1",
                "market_probability": 0.61,
                "confidence_adjusted_gap": 0.04,
                "comparison_status": "aligned",
                "model_band": "35",
                "market_band": "35",
                "top_parameter_view": {
                    "schema_version": "top_parameter_view.v1",
                    "market_id": "m1",
                    "market_family": "temperature_daily_max",
                    "market_question": "Will Shanghai exceed 35C?",
                    "location_name": "Shanghai",
                    "target_date": "2026-04-20",
                    "variable_name": "daily_max_temperature",
                    "polymarket": {
                        "yes_price": 0.64,
                        "no_price": 0.36,
                        "market_implied_probability": 0.64,
                        "favored_side": "yes",
                        "market_band": "35",
                    },
                    "weather": {
                        "observation_value": 34.2,
                        "forecast_value": 34.8,
                        "unit": "celsius",
                        "model_band": "35",
                        "official_band": "35",
                        "station_name": "Shanghai Pudong Intl Airport Station",
                        "station_id": "ZSPD",
                        "observed_at": "2026-04-19T08:30:00Z",
                        "forecast_timestamp": "2026-04-19T09:00:00Z",
                    },
                    "source_contract": {
                        "settlement_source_type": "station_observation",
                        "official_vs_proxy_source": "official",
                        "source_match_grade": "exact_station",
                        "required_sources": ["metar", "wunderground"],
                        "official_source_url": "https://example.com",
                        "freshness_status": "fresh",
                    },
                    "decision": {
                        "fair_value": 0.71,
                        "edge": 0.08,
                        "probability_mode": "shadow_calibrated_candidate",
                        "execution_constraint": "dry_run_only",
                        "can_execute": "no",
                        "primary_block_reason": "shadow_only",
                        "recommended_operator_action": "refresh_pipeline_inputs",
                        "comparison_status": "aligned",
                    },
                },
            },
            {
                "timestamp": "2026-04-19T10:00:00Z",
                "market_id": "m1",
                "market_probability": 0.64,
                "confidence_adjusted_gap": 0.08,
                "comparison_status": "aligned",
                "model_band": "35",
                "market_band": "35",
                "top_parameter_view": {
                    "schema_version": "top_parameter_view.v1",
                    "market_id": "m1",
                    "market_family": "temperature_daily_max",
                    "market_question": "Will Shanghai exceed 35C?",
                    "location_name": "Shanghai",
                    "target_date": "2026-04-20",
                    "variable_name": "daily_max_temperature",
                    "weather": {
                        "observation_value": 34.4,
                        "forecast_value": 35.1,
                        "station_id": "ZSPD",
                        "freshness_status": "fresh",
                    },
                    "source_contract": {
                        "source_match_grade": "exact_station",
                        "freshness_status": "fresh",
                    },
                    "decision": {
                        "can_execute": "yes",
                        "primary_block_reason": "none",
                    },
                },
            },
            {
                "timestamp": "2026-04-19T10:00:00Z",
                "market_id": "m2",
                "market_probability": 0.2,
                "confidence_adjusted_gap": -0.1,
                "comparison_status": "aligned",
            },
        ]
    )

    summary = build_history_relationship_summary(history_df, "m1")

    assert summary is not None
    assert summary["top_parameter_view"]["schema_version"] == "top_parameter_view.v1"
    assert summary["top_parameter_view"]["weather"]["forecast_value"] == 35.1
    assert summary["top_parameter_view"]["source_contract"]["source_match_grade"] == "exact_station"
    assert summary["top_parameter_view"]["decision"]["can_execute"] == "yes"
    assert list(summary["preview"].columns) == [
        "timestamp",
        "market_probability",
        "confidence_adjusted_gap",
        "comparison_status",
        "model_band",
        "market_band",
    ]
    assert str(summary["working"].iloc[-1]["timestamp"]).startswith("2026-04-19 10:00:00")
