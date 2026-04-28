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
            "source_priority": "high",
            "source_policy_ref": "wunderground_station",
            "precision_policy_ref": "precision_policy.temperature_daily_max.v1",
            "rounding_policy_ref": "rounding_policy.temperature_daily_max.v1",
            "band_mapping_policy_ref": "band_mapping.temperature_celsius_integer.v1",
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
        validation_freshness_status={
            "status": "healthy",
            "reason": "validation_report_fresh",
            "freshness_seconds": 1800,
        },
        observation_snapshot={
            "observation_value": 29.1,
            "observation_band": "29",
            "observed_at": "2026-04-19T09:30:00Z",
            "station_name": "Shanghai Pudong Intl Airport Station",
            "station_id": "ZSPD",
            "settlement_ready": False,
        },
    )

    assert summary["schema_version"] == "top_parameter_view.v2"
    assert summary["market_id"] == "m1"
    assert summary["market_family"] == "temperature_daily_max"
    assert len(summary["cards"]) == 5
    assert summary["cards"][2]["title"] == "Weather / Forecast Params"
    assert summary["cards"][2]["metric_label"] == "Live Temp vs Forecast"
    assert "Obs 29.1" in str(summary["cards"][2]["metric_value"])
    assert summary["cards"][3]["metric_value"] == "exact_station"
    assert summary["cards"][4]["metric_value"] == "no"
    assert any(row[0] == "Obs Temp" for row in summary["cards"][2]["rows"])
    assert any(row[0] == "Canonical Unit" for row in summary["cards"][2]["rows"])
    assert any(row[0] == "Realtime Compare" for row in summary["cards"][2]["rows"])
    assert any(row[0] == "Forecast Reason" for row in summary["cards"][2]["rows"])
    assert any(row[0] == "Freshness Reason" for row in summary["cards"][2]["rows"])
    assert any(row[0] == "Source Priority" for row in summary["cards"][3]["rows"])
    assert any(row[0] == "Fallback Mode" for row in summary["cards"][3]["rows"])
    assert any(row[0] == "Source Policy Ref" for row in summary["cards"][3]["rows"])
    assert any(row[0] == "Settlement Ready" for row in summary["cards"][2]["rows"])


def test_top_parameter_ribbon_summary_derives_market_probability_from_yes_no_prices():
    summary = build_top_parameter_ribbon_summary(
        market_snapshot={
            "market_id": "m2",
            "market_question": "Will Shanghai exceed 35C?",
            "market_family": "temperature_daily_max",
            "location_name": "Shanghai",
            "target_date": "2026-04-20",
            "variable_name": "daily_max_temperature",
            "yes_price": 0.64,
            "no_price": 0.36,
            "favored_side": "yes",
            "market_band": "35",
        },
        forecast_snapshot={},
        resolver_rule={},
        probability_state={},
        comparison_row={},
        compact_gate_summary={},
        observation_snapshot={},
    )

    polymarket_card = next(card for card in summary["cards"] if card["title"] == "Polymarket Params")
    assert polymarket_card["metric_value"] == 0.64


def test_top_parameter_ribbon_summary_explains_forecast_unavailable_and_blocked_freshness():
    summary = build_top_parameter_ribbon_summary(
        market_snapshot={
            "market_id": "m3",
            "market_question": "Will Shanghai exceed 35C?",
            "market_family": "temperature_daily_max",
            "location_name": "Shanghai",
            "target_date": "2026-04-20",
            "variable_name": "daily_max_temperature",
            "market_band": "35",
        },
        forecast_snapshot={
            "source_mode": "Target-date forecast unavailable",
        },
        resolver_rule={
            "market_id": "m3",
            "station_name": "Shanghai Pudong Intl Airport Station",
            "station_id": "ZSPD",
            "required_sources": ["metar", "wunderground"],
            "source_match_grade": "exact_station",
        },
        probability_state={},
        comparison_row={},
        compact_gate_summary={
            "gate_status": "BLOCKED",
            "validation_freshness_status": "blocked",
            "blockers": ["validation_freshness_blocked"],
            "recommended_operator_action": "refresh_validation_reports",
            "freshness_gate": "blocked",
        },
        validation_freshness_status={
            "status": "blocked",
            "reason": "validation_report_stale",
            "freshness_seconds": 90000,
        },
        observation_snapshot={
            "observation_value": 29.1,
            "canonical_value": 29.1,
            "observation_canonical_value": 29.1,
            "observation_band": "29",
            "observed_at": "2026-04-20T21:47:03+0800",
            "station_name": "Shanghai Pudong Intl Airport Station",
            "station_id": "ZSPD",
            "settlement_ready": False,
        },
    )

    weather_card = next(card for card in summary["cards"] if card["title"] == "Weather / Forecast Params")
    gate_card = next(card for card in summary["cards"] if card["title"] == "Comparison / Gate Summary")
    assert "forecast unavailable" in str(weather_card["rows"][2][1]).lower()
    assert "forecast row missing for target date" in str(weather_card["rows"][3][1]).lower()
    assert "validation freshness is blocked" in str(weather_card["rows"][4][1]).lower()
    assert any(row[0] == "Freshness Reason" for row in gate_card["rows"])
    assert any(row[0] == "Freshness Age" for row in gate_card["rows"])
