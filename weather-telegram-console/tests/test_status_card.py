from weather_telegram_console.bot.formatters.status_card import format_status_card


def test_format_status_card() -> None:
    report = {
        "overall_status": "guarded",
        "generated_at": "2026-04-18T09:00:00+00:00",
        "current_market": {
            "market_id": "678686",
            "market_question": "Will 2026 be the hottest year on record?",
            "comparison_status": "aligned",
            "action_hint": "watch",
        },
        "top_parameter_view": {
            "schema_version": "top_parameter_view.v1",
            "market_id": "678686",
            "market_family": "temperature_daily_max",
            "market_question": "Will 2026 be the hottest year on record?",
            "location_name": "Global",
            "target_date": "2026-12-31",
            "variable_name": "global_temperature_index",
            "polymarket": {
                "yes_price": 0.61,
                "no_price": 0.39,
                "market_implied_probability": 0.61,
                "favored_side": "yes",
                "market_band": "1.5C",
            },
            "weather": {
                "observation_value": 1.42,
                "forecast_value": 1.48,
                "unit": "celsius",
                "canonical_unit": "celsius",
                "model_band": "1.5C",
                "official_band": "1.5C",
                "station_name": "Global Dataset",
                "station_id": "GLOBAL",
                "observed_at": "2026-04-18T09:00:00+00:00",
                "forecast_timestamp": "2026-04-18T09:05:00+00:00",
            },
            "source_contract": {
                "settlement_source_type": "dataset",
                "official_vs_proxy_source": "official",
                "source_match_grade": "exact_station",
                "required_sources": "metar, wunderground",
                "official_source_url": "https://example.com",
                "freshness_status": "healthy",
                "source_priority": "high",
                "fallback_mode": "official",
                "source_policy_ref": "wunderground_station",
                "precision_policy_ref": "precision_policy.global_temperature_index.v1",
                "rounding_policy_ref": "rounding_policy.global_temperature_index.v1",
                "band_mapping_policy_ref": "band_mapping.global_temperature_index_ordinal.v1",
            },
            "decision": {
                "fair_value": 0.64,
                "edge": 0.03,
                "probability_mode": "heuristic_not_calibrated",
                "execution_constraint": "manual_advisory_only",
                "can_execute": "no",
                "primary_block_reason": "shadow_only",
                "recommended_operator_action": "hold_execution_and_review",
                "comparison_status": "aligned",
            },
        },
        "monitoring": {
            "overall_status": "healthy",
            "worker_count": 3,
            "counts": {"healthy": 3, "warning": 0, "stale": 0, "missing": 0},
            "workers": [
                {"label": "Market", "status": "healthy"},
                {"label": "Forecast", "status": "healthy"},
            ],
        },
        "source_policy": {
            "overall_status": "healthy",
            "fresh_count": 3,
            "stale_count": 0,
            "unavailable_count": 0,
            "priority_counts": {"high": 2, "medium": 1},
            "problem_sources": [],
        },
        "validation": {
            "freshness_status": "healthy",
            "label_coverage_status": "healthy",
            "validation_sample_count": 124,
            "validation_labeled_sample_count": 96,
            "calibration_status": "calibrated",
            "source_coverage": 1.0,
            "normalization_coverage": 1.0,
            "coverage_blockers": [],
            "validation_assimilation_summary": {
                "assimilation_status": "healthy",
                "feature_store_ready": True,
                "label_store_ready": True,
                "backtest_ready": True,
                "top_watchlist_family": "sea_ice_extent",
                "top_watchlist_reason": "drift_spike+drift=0.0875",
            },
            "family_rollout_summary": {
                "coverage_ratio": 1.0,
                "ready_ratio": 0.5,
                "top_family": "station_temperature",
                "top_drift_family": "sea_ice_extent",
            },
            "family_rollout_trend_summary": {
                "sample_count": 3,
                "bucket_count": 2,
                "trend_windows": [
                    {"window_label": "window_1"},
                    {"window_label": "window_2"},
                ],
                "coverage_movement": 0.5,
                "ready_movement": 0.5,
                "drift_movement": 0.03,
            },
            "family_rollout_watchlist": {
                "watchlist_count": 2,
                "stalled_family_count": 1,
                "drift_spike_family_count": 1,
                "expansion_backlog_count": 1,
                "top_watchlist_family": "sea_ice_extent",
                "top_watchlist_attention_level": "critical",
                "top_watchlist_reason": "drift_spike+drift=0.0875",
            },
            "family_anomaly_summary": {
                "schema_version": "family_anomaly_summary.v1",
                "family_scan_status": "canonical_only",
                "top_family": "sea_ice_extent",
                "top_score": 0.89,
                "top_bucket": "high",
                "signal_summary": "pv=1 edge=2 mismatch=0 stress=2 peer=1 high=2",
                "bucket_counts": {"high": 1, "medium": 0, "low": 0},
                "generated_at": "2026-04-21T10:00:00+00:00",
            },
        },
        "probability": {
            "contract_version": "probability_contract.v1",
            "probability_mode": "heuristic_not_calibrated",
            "execution_constraint": "manual_advisory_only",
            "calibration_status": "not_calibrated",
            "confidence_adjusted_edge": 0.04,
            "promotion_state": {
                "schema_version": "promotion_state.v1",
                "probability_mode": "heuristic_not_calibrated",
                "base_probability_mode": "heuristic_not_calibrated",
                "execution_constraint": "manual_advisory_only",
                "base_execution_constraint": "manual_advisory_only",
                "promotion_reason": "thresholds_not_met",
                "demotion_reason": "validation_freshness_unhealthy",
                "approved_for_live": False,
            },
        },
        "execution": {
            "status": "blocked",
            "ready_for_live": False,
            "decision": "LIVE_EXECUTION_BLOCKED",
            "blocking_count": 2,
        },
        "operator": {
            "can_bot_trade": False,
            "human_action_required": True,
            "execution_mode": "manual_advisory_only",
            "operator_mode": "dry_run_guarded",
            "mode_badge": {"label": "DRY-RUN GUARDED"},
        },
        "gate_stack": {
            "data_gate": "pass",
            "resolver_gate": "blocked",
            "probability_gate": "blocked",
            "freshness_gate": "pass",
            "authorization_gate": "blocked",
            "execution_gate": "blocked",
        },
        "block_reasons": [
            "probability_mode:heuristic_not_calibrated",
            "execution:blocked",
        ],
    }

    text = format_status_card(report)

    assert "AARS Unified Status" in text
    assert "Top Parameter Surface" in text
    assert "Operator Summary" in text
    assert "Weather / Forecast Params" in text
    assert "Live Temp vs Forecast" in text
    assert "Obs Temp" in text
    assert "Next Step" in text
    assert "heuristic_not_calibrated" in text
    assert "LIVE_EXECUTION_BLOCKED" in text
    assert "Will 2026 be the hottest year on record?" in text
    assert "DRY-RUN GUARDED" in text
    assert "probability_contract.v1" in text
    assert "Promotion State" in text
    assert "Family Rollout" in text
    assert "Family Rollout Trend" in text
    assert "Family Rollout Watchlist" in text
    assert "Advanced Anomaly" in text
    assert "sea_ice_extent" in text
    assert "Source Policy" in text
    assert "Validation" in text
    assert "Assimilation Status" in text
    assert "Feature Store Ready" in text
    assert "Family Coverage" in text
    assert "Rollout Top Family" in text
    assert "Canonical Unit" in text
    assert "Source Priority" in text
    assert "Forecast Reason" in text
    assert "Freshness Reason" in text
    assert "validation_freshness_unhealthy" in text
    assert "Gate Stack" in text
    assert "Authorization Gate" in text
