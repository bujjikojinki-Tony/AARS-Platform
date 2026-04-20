from weather_dashboard.ui.top_parameter_ribbon import build_top_parameter_ribbon_summary


def test_top_parameter_ribbon_summary_surfaces_weather_and_gate_context():
    summary = build_top_parameter_ribbon_summary(
        market_snapshot={
            "market_id": "m1",
            "market_question": "Will Shanghai exceed 35C?",
            "market_family": "temperature_daily_max",
            "location_name": "Shanghai",
            "target_date": "2026-04-20",
            "variable_name": "daily_max_temperature",
            "market_probability": 0.62,
            "yes_price": 0.64,
            "no_price": 0.36,
            "favored_side": "yes",
            "market_band": "35",
        },
        forecast_snapshot={
            "value": 34.8,
            "model_band": "35",
            "station_name": "Shanghai Pudong Intl Airport Station",
            "station_id": "ZSPD",
            "timestamp": "2026-04-19T10:00:00Z",
            "source_mode": "rule",
            "required_data_source": "metar",
        },
        resolver_rule={
            "resolver_status": "matched",
            "settlement_source_type": "station_observation",
            "official_vs_proxy_source": "official",
            "source_match_grade": "exact_station",
            "required_sources": ["metar", "wunderground"],
        },
        probability_state={
            "fair_value": 0.71,
            "confidence_adjusted_edge": 0.08,
            "probability_mode": "shadow_calibrated_candidate",
            "execution_constraint": "dry_run_only",
        },
        comparison_row={
            "comparison_status": "aligned",
            "action_hint": "watch",
        },
        compact_gate_summary={
            "gate_status": "BLOCKED",
            "validation_freshness_status": "healthy",
            "blockers": ["shadow_only"],
            "recommended_operator_action": "refresh_pipeline_inputs",
            "freshness_gate": "pass",
        },
        shanghai_live_weather={
            "observed_temp_c": 29.1,
            "observed_valid_time": "2026-04-19T09:30:00Z",
            "station_name": "Shanghai Pudong Intl Airport Station",
            "station_code": "ZSPD",
        },
    )

    assert summary["schema_version"] == "top_parameter_ribbon.v1"
    assert summary["market_id"] == "m1"
    assert summary["market_family"] == "temperature_daily_max"
    assert len(summary["cards"]) == 5
    assert summary["cards"][2]["title"] == "Weather Params"
    assert summary["cards"][2]["metric_value"] == 34.8
    assert summary["cards"][3]["metric_value"] == "exact_station"
    assert summary["cards"][4]["metric_value"] == "no"
    assert any(row[0] == "Observation Value" for row in summary["cards"][2]["rows"])
