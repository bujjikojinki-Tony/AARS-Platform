from weather_telegram_console.bot.formatters.monitoring_card import format_monitoring_card


def test_format_monitoring_card() -> None:
    text = format_monitoring_card(
        {
            "alert_count": 2,
            "family_scan_count": 1,
            "anomaly_event_count": 3,
            "latest_source_policy_status": {
                "overall_status": "healthy",
                "counts": {"fresh": 3, "stale": 1, "unavailable": 0},
                "priority_counts": {"high": 2, "medium": 1},
                "problem_sources": [
                    {"source_name": "metar", "freshness_status": "stale", "status_reason": "past_fresh_threshold"}
                ],
                "sources": [
                    {"source_name": "metar", "priority_level": "high", "fallback_policy": "fallback_to_last_observation"},
                    {"source_name": "ecmwf", "priority_level": "high", "fallback_policy": "fallback_to_previous_run"},
                ],
            },
            "latest_alert": {
                "market_id": "693874",
                "market_family": "sea_ice_extent",
                "severity": "amber",
                "primary_reason": "strong_divergence_or_reaction_gap",
                "recommended_operator_action": "review_market_now",
                "generated_at": "2026-04-21T03:33:44+00:00",
            },
            "latest_family_scan_report": {
                "family_count": 1,
                "market_count": 1,
                "signal_summary": {
                    "price_velocity_high_count": 1,
                    "edge_dislocation_high_count": 1,
                    "evidence_mismatch_count": 0,
                    "microstructure_stress_high_count": 1,
                    "peer_outlier_count": 0,
                    "intervention_like_high_count": 1,
                },
                "anomaly_bucket_counts": {"high": 1, "medium": 0, "low": 0},
                "generated_at": "2026-04-21T03:33:44+00:00",
                "family_summaries": [
                    {
                        "market_family": "sea_ice_extent",
                        "max_intervention_like_score": 0.37,
                        "signal_summary": {
                            "price_velocity_high_count": 1,
                            "edge_dislocation_high_count": 1,
                            "evidence_mismatch_count": 0,
                            "microstructure_stress_high_count": 1,
                            "peer_outlier_count": 0,
                            "intervention_like_high_count": 1,
                        },
                    }
                ],
            },
            "latest_anomaly_event": {
                "market_id": "693874",
                "market_family": "sea_ice_extent",
                "anomaly_score": 0.41,
                "intervention_like_score": 0.37,
                "anomaly_bucket": "low",
                "primary_reason": "edge_dislocation",
                "feature_breakdown": {
                    "price_velocity": 0.12,
                    "edge_dislocation": 0.11,
                    "evidence_mismatch_score": 0.0,
                    "microstructure_stress_score": 0.7,
                    "peer_rank": 1,
                    "peer_zscore": 0.0,
                    "peer_outlier_flag": False,
                },
                "generated_at": "2026-04-21T03:33:44+00:00",
            },
            "runtime_block": {
                "overall_status": "blocked",
                "gate_status": "blocked",
                "execution_status": "blocked",
                "ready_for_live": False,
                "can_execute": False,
                "primary_block_reason": "comparison_not_actionable",
                "recommended_operator_action": "hold_execution_and_review",
                "block_reason_count": 4,
            },
            "operator_summary": {
                "schema_version": "operator_summary.v1",
                "current_focus": "693874",
                "current_family": "sea_ice_extent",
                "alert_severity": "amber",
                "anomaly_bucket": "low",
                "gate_status": "blocked",
                "recommended_operator_action": "review_gate_block",
                "primary_reason": "comparison_not_actionable",
            },
        }
    )

    assert "AARS Monitoring Signals" in text
    assert "Alert Count" in text
    assert "Latest Market Alert" in text
    assert "Gate / Runtime Block" in text
    assert "Source Policy" in text
    assert "Fallback Policies" in text
    assert "Signal Summary" in text
    assert "Bucket Counts" in text
    assert "Operator Summary" in text
    assert "693874" in text
