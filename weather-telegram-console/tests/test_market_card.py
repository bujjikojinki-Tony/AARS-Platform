from weather_telegram_console.bot.formatters.market_card import format_market_card


def test_format_market_card() -> None:
    text = format_market_card(
        {
            "market_id": "mkt_123",
            "market_question": "Will NYC hit 95F?",
            "location_name": "New York City",
            "target_date": "2026-07-04",
            "variable_name": "temperature_max",
            "top_parameter_view": {
                "schema_version": "top_parameter_view.v1",
                "market_id": "mkt_123",
                "market_family": "temperature_daily_max",
                "market_question": "Will NYC hit 95F?",
                "location_name": "New York City",
                "target_date": "2026-07-04",
                "variable_name": "temperature_max",
                "polymarket": {
                    "yes_price": 0.41,
                    "no_price": 0.59,
                    "market_implied_probability": 0.41,
                    "favored_side": "yes",
                    "market_band": "91-95F",
                },
                "weather": {
                    "observation_value": 92.5,
                    "forecast_value": 93.2,
                    "unit": "celsius",
                    "canonical_unit": "celsius",
                    "model_band": "91-95F",
                    "official_band": "91-95F",
                    "station_name": "Central Park",
                    "station_id": "USW00094728",
                    "observed_at": "2026-04-18T09:00:00+00:00",
                    "forecast_timestamp": "2026-04-18T09:05:00+00:00",
                },
                "source_contract": {
                    "settlement_source_type": "station_observation",
                    "official_vs_proxy_source": "official",
                    "source_match_grade": "exact_station",
                    "required_sources": "metar, wunderground",
                    "official_source_url": "https://example.com",
                    "freshness_status": "healthy",
                    "source_priority": "high",
                    "fallback_mode": "official",
                    "source_policy_ref": "wunderground_station",
                    "precision_policy_ref": "precision_policy.temperature_daily_max.v1",
                    "rounding_policy_ref": "rounding_policy.temperature_daily_max.v1",
                    "band_mapping_policy_ref": "band_mapping.temperature_celsius_integer.v1",
                },
                "decision": {
                    "fair_value": 0.53,
                    "edge": 0.12,
                    "probability_mode": "shadow_calibrated_candidate",
                    "execution_constraint": "dry_run_only",
                    "can_execute": "no",
                    "primary_block_reason": "shadow_only",
                    "recommended_operator_action": "refresh_pipeline_inputs",
                    "comparison_status": "aligned",
                },
            },
            "yes_price": 0.41,
            "no_price": 0.59,
            "market_probability": 0.41,
            "market_band": "91-95F",
            "model_value": 93.2,
            "model_band": "91-95F",
            "confidence_score": 0.77,
            "confidence_adjusted_gap": 0.06,
            "comparison_status": "aligned",
            "action_hint": "watch",
            "comparison_reason": "Bands aligned.",
            "rule_status": "eligible",
            "promotion_state": {
                "schema_version": "promotion_state.v1",
                "probability_mode": "shadow_calibrated_candidate",
                "base_probability_mode": "heuristic_not_calibrated",
                "execution_constraint": "dry_run_only",
                "base_execution_constraint": "manual_advisory_only",
                "promotion_reason": "candidate_thresholds_passed",
                "demotion_reason": None,
            },
            "market_snapshot_ref": "2026-04-18T09:00:00+00:00",
            "forecast_snapshot_ref": "2026-04-18T09:05:00+00:00",
            "compact_gate_stack": {
                "resolver_gate": "blocked",
                "resolver_gate_reasons": ["resolver_confidence_low"],
            },
            "advisory_summary": {
                "event_count": 1,
                "latest_event_type": "operator_acknowledged_manual_advisory",
                "latest_created_at": "2026-04-18T09:10:00+00:00",
                "latest_decision": "operator_acknowledged",
                "latest_gate_status": None,
                "latest_price": 0.44,
                "latest_size": 12,
            },
            "data_availability": {
                "manual_advisory_audit_available": True,
            },
            "workstation_context": {
                "schema_version": "telegram_market_workstation_context.v1",
                "market_alert": {
                    "severity": "amber",
                    "primary_reason": "forecast_divergence",
                    "recommended_operator_action": "review_market_alert",
                },
                "family_anomaly": {
                    "anomaly_score": 0.71,
                    "anomaly_bucket": "medium",
                    "primary_reason": "edge_dislocation",
                },
                "family_anomaly_summary": {
                    "schema_version": "family_anomaly_summary.v1",
                    "family_scan_status": "canonical_only",
                    "top_family": "sea_ice_extent",
                    "top_score": 0.91,
                    "top_bucket": "high",
                    "signal_summary": "pv=1 edge=2 mismatch=0 stress=2 peer=1 high=2",
                },
                "gate_summary": {
                    "execution_boundary": "gate_stack_api.v1_only",
                    "execution_gate": "blocked",
                    "primary_block_reason": "manual_advisory_only",
                    "recommended_operator_action": "hold_execution_and_review",
                },
                "validation_summary": {
                    "promotion_state": "shadow_calibrated_candidate",
                    "freshness_status": "blocked",
                    "freshness_reason": "validation_report_stale",
                    "coverage_status": "blocked",
                    "labeled_ratio": 0.1,
                    "calibration_status": "not_calibrated",
                },
                "opportunity_entry": {
                    "row_id": "New York.temperature_daily_max",
                    "opportunity_score": 0.82,
                    "difficulty_label": "medium",
                    "recommended_action": "open_workstation",
                    "best_model": "NOAA",
                    "best_source_stack": ["hrrr", "metar", "official_obs"],
                },
            },
        }
    )

    assert "AARS Market Snapshot" in text
    assert "Top Parameter Surface" in text
    assert "Market Identity" in text
    assert "Weather / Forecast Params" in text
    assert "Live Temp vs Forecast" in text
    assert "Obs Temp" in text
    assert "Will NYC hit 95F?" in text
    assert "93.2" in text
    assert "Forecast Reason" in text
    assert "Freshness Reason" in text
    assert "Bands aligned." in text
    assert "Promotion State" in text
    assert "candidate_thresholds_passed" in text
    assert "2026-04-18T09:05:00+00:00" in text
    assert "Resolver Gate" in text
    assert "resolver_confidence_low" in text
    assert "Canonical Unit" in text
    assert "Source Priority" in text
    assert "Fallback Mode" in text
    assert "audit events recorded" in text
    assert "Single Market Workstation" in text
    assert "Market Alert" in text
    assert "forecast_divergence" in text
    assert "Family Anomaly" in text
    assert "edge_dislocation" in text
    assert "Advanced Anomaly Snapshot" in text
    assert "sea_ice_extent" in text
    assert "Gate Boundary" in text
    assert "gate_stack_api.v1_only" in text
    assert "Validation / Coverage" in text
    assert "Opportunity Entry" in text
    assert "open_workstation" in text


def test_format_market_card_shows_missing_audit_file_hint() -> None:
    text = format_market_card(
        {
            "market_id": "mkt_404",
            "advisory_summary": {"event_count": 0},
            "data_availability": {"manual_advisory_audit_available": False},
        }
    )

    assert "manual advisory audit file is not available" in text
