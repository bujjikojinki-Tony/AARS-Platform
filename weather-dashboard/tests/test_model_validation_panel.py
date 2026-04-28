from weather_dashboard.ui.model_validation_panel import build_validation_summary, _validation_tone


def test_validation_summary_surfaces_promotion_blockers():
    summary = build_validation_summary(
        {
            "approved_for_live": False,
            "deployment_mode": "shadow",
            "calibration_status": "not_calibrated",
            "probability_mode": "heuristic_not_calibrated",
            "promotion_state": {
                "probability_mode": "heuristic_not_calibrated",
                "promotion_reason": "validation_report_stale",
                "demotion_reason": "validation_freshness_blocked",
            },
            "sample_count": 100,
            "labeled_sample_count": 12,
            "validation_metrics": {
                "brier_score": 0.22,
                "calibration_error": 0.18,
                "roi_backtest": -0.03,
            },
            "resolver_quality": {
                "resolver_match_rate": 0.8,
                "unmatched_count": 2,
            },
            "governance_summary": {
                "canonical_ratio": 1.0,
                "source_policy_coverage": 1.0,
                "normalization_coverage": 1.0,
            },
            "family_rollout_summary": {
                "family_count": 2,
                "coverage_ratio": 1.0,
                "ready_ratio": 0.5,
                "ready_family_count": 1,
                "top_family": "station_temperature",
                "top_drift_family": "sea_ice_extent",
                "top_drift_value": 0.04,
                "drift_bucket_counts": {"low": 1, "medium": 1, "high": 0},
                "family_summaries": [
                    {
                        "market_family": "station_temperature",
                        "sample_count": 2,
                        "coverage_status": "healthy",
                        "calibration_error": 0.12,
                        "drift_from_global": 0.01,
                        "drift_bucket": "low",
                    },
                    {
                        "market_family": "sea_ice_extent",
                        "sample_count": 1,
                        "coverage_status": "warning",
                        "calibration_error": 0.16,
                        "drift_from_global": 0.04,
                        "drift_bucket": "medium",
                    },
                ],
            },
            "family_rollout_trend_summary": {
                "sample_count": 3,
                "bucket_count": 2,
                "trend_windows": [
                    {
                        "window_label": "window_1",
                        "sample_count": 1,
                        "coverage_ratio": 0.5,
                        "ready_ratio": 0.0,
                        "top_family": "station_temperature",
                        "top_drift_family": "station_temperature",
                        "top_drift_value": 0.01,
                    },
                    {
                        "window_label": "window_2",
                        "sample_count": 2,
                        "coverage_ratio": 1.0,
                        "ready_ratio": 0.5,
                        "top_family": "sea_ice_extent",
                        "top_drift_family": "sea_ice_extent",
                        "top_drift_value": 0.04,
                    },
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
                "watchlist": [
                    {
                        "watchlist_rank": 1,
                        "market_family": "sea_ice_extent",
                        "attention_level": "critical",
                        "coverage_status": "stalled",
                        "drift_bucket": "high",
                        "sample_count": 1,
                        "suggested_action": "prioritize_backfill_and_resolver_review",
                    },
                    {
                        "watchlist_rank": 2,
                        "market_family": "station_temperature",
                        "attention_level": "medium",
                        "coverage_status": "healthy",
                        "drift_bucket": "low",
                        "sample_count": 2,
                        "suggested_action": "continue_monitoring",
                    },
                ],
            },
            "validation_assimilation_summary": {
                "assimilation_status": "blocked",
                "feature_store_ready": False,
                "label_store_ready": False,
                "backtest_ready": False,
                "primary_blocker": "calibration:not_calibrated",
                "top_watchlist_family": "sea_ice_extent",
                "top_watchlist_attention_level": "critical",
                "top_watchlist_reason": "drift_spike+drift=0.0875",
            },
        },
        {"model_probability": {"reliability_curve": [{"bucket": 1}]}},
        {"trade_count": 5, "roi": 0.01},
        {"status": "blocked", "freshness_seconds": 999},
        {"status": "blocked", "labeled_ratio": 0.12, "minimum_labeled_rows": 30},
        {
            "schema_version": "family_scan_report.v1",
            "generated_at": "2026-04-21T01:00:00+00:00",
            "input_mode": "canonical_only",
            "family_summaries": [
                {
                    "market_family": "sea_ice_extent",
                    "market_count": 3,
                    "average_intervention_like_score": 0.72,
                    "max_intervention_like_score": 0.87,
                    "outlier_count": 2,
                    "signal_summary": "pv=1 edge=2 mismatch=0 stress=2 peer=1 high=2",
                }
            ],
            "signal_summary": {
                "price_velocity_high_count": 1,
                "edge_dislocation_high_count": 2,
                "evidence_mismatch_count": 0,
                "microstructure_stress_high_count": 2,
                "peer_outlier_count": 1,
                "intervention_like_high_count": 2,
            },
            "anomaly_bucket_counts": {"high": 2, "medium": 1, "low": 0},
        },
    )

    assert summary["approved_for_live"] is False
    assert summary["coverage_status"] == "blocked"
    assert summary["freshness_status"] == "blocked"
    assert summary["promotion_state"] == "heuristic_not_calibrated"
    assert summary["promotion_reason"] == "validation_report_stale"
    assert summary["demotion_reason"] == "validation_freshness_blocked"
    assert summary["calibration_curve_points"] == 1
    assert summary["canonical_ratio"] == 1.0
    assert summary["source_policy_coverage"] == 1.0
    assert summary["family_coverage_ratio"] == 1.0
    assert summary["family_ready_ratio"] == 0.5
    assert summary["top_family"] == "station_temperature"
    assert summary["trend_window_count"] == 2
    assert summary["coverage_movement"] == 0.5
    assert summary["ready_movement"] == 0.5
    assert summary["drift_movement"] == 0.03
    assert summary["watchlist_count"] == 2
    assert summary["stalled_family_count"] == 1
    assert summary["drift_spike_family_count"] == 1
    assert summary["expansion_backlog_count"] == 1
    assert summary["top_watchlist_family"] == "sea_ice_extent"
    assert summary["top_watchlist_attention_level"] == "critical"
    assert summary["top_watchlist_reason"] == "drift_spike+drift=0.0875"
    assert summary["assimilation_status"] == "blocked"
    assert summary["feature_store_ready"] is False
    assert summary["family_scan_status"] == "canonical_only"
    assert summary["family_scan_top_family"] == "sea_ice_extent"
    assert summary["family_scan_top_score"] == 0.87
    assert summary["family_scan_top_bucket"] == "high"
    assert "pv=1" in summary["family_scan_signal_summary"]
    assert summary["family_scan_bucket_counts"] == {"high": 2, "medium": 1, "low": 0}
    assert "not_approved_for_live" in summary["blockers"]
    assert "calibration:not_calibrated" in summary["blockers"]


def test_validation_summary_surfaces_phase30_artifacts():
    summary = build_validation_summary(
        {
            "approved_for_live": True,
            "deployment_mode": "shadow",
            "calibration_status": "calibrated",
        },
        None,
        None,
        {"status": "healthy", "freshness_seconds": 120},
        {"status": "healthy", "labeled_ratio": 0.9},
        {
            "schema_version": "family_anomaly_summary.v1",
            "generated_at": "2026-04-22T12:00:00+00:00",
            "market_family": "sea_ice_extent",
            "high_intervention_like_count": 1,
            "family_risk_summary": "moderate_family_anomaly_risk",
        },
        {
            "schema_version": "validation_summary.v1",
            "generated_at": "2026-04-22T11:00:00+00:00",
            "scope_type": "family",
            "scope_id": "all",
            "validation_status": "strong",
            "validation_age": "1h",
            "label_coverage": 0.9,
            "source_coverage": 0.85,
            "normalization_consistency": 1.0,
            "family_support_level": "strong",
            "promotion_readiness": "ready",
            "reasons": ["fresh labels"],
        },
        {
            "schema_version": "coverage_summary.v1",
            "label_coverage": 0.9,
            "source_coverage": 0.85,
            "normalization_consistency": 1.0,
        },
        {
            "schema_version": "promotion_decision_support.v1",
            "current_probability_mode": "shadow_calibrated_candidate",
            "promotion_readiness": "ready",
            "promotion_reason": "ready_for_live",
        },
        {
            "schema_version": "model_validation_compare.v1",
            "selected_best_model": "ECMWF",
            "selected_best_source_stack": ["ecmwf", "official_obs"],
        },
    )

    assert summary["validation_summary_status"] == "strong"
    assert summary["validation_summary_promotion_readiness"] == "ready"
    assert summary["family_scan_top_family"] == "sea_ice_extent"
    assert summary["model_validation_compare_best_model"] == "ECMWF"


def test_validation_tone_maps_statuses():
    assert _validation_tone("healthy") == "ok"
    assert _validation_tone("blocked") == "block"
    assert _validation_tone("warning") == "warn"
    assert _validation_tone("unknown") == "neutral"
