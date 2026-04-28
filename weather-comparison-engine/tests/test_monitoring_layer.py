from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from weather_comparison_engine.monitoring_layer import (
    build_family_scan_report,
    build_market_alert_event,
    build_observation_shock_result,
    write_family_scan_report,
    write_market_alert_event,
)


def test_build_observation_shock_result_uses_explicit_threshold_cross_value() -> None:
    result = build_observation_shock_result(
        observation_snapshot={
            "observation_value": 31.0,
            "observation_canonical_value": 31.0,
            "observed_at": "2026-04-21T10:00:00Z",
            "source_match_grade": "exact_station",
        },
        previous_observation_snapshot={
            "observation_value": 29.0,
            "observation_canonical_value": 29.0,
            "observed_at": "2026-04-21T09:30:00Z",
        },
        threshold_policy={
            "threshold_value": {"threshold_cross_value": 30.0},
        },
        source_match_grade="exact_station",
    )

    assert result["threshold_cross_value"] == 30.0
    assert result["threshold_cross_event"] is True
    assert result["threshold_cross_direction"] == "up"
    assert result["review_only"] is False


def test_build_market_alert_event_includes_monitoring_signals(tmp_path: Path) -> None:
    event = build_market_alert_event(
        market_id="m-1",
        observation_snapshot={
            "market_id": "m-1",
            "observation_value": 31.0,
            "observation_canonical_value": 31.0,
            "observed_at": "2026-04-21T10:00:00Z",
            "source_match_grade": "exact_station",
        },
        forecast_snapshot={
            "market_id": "m-1",
            "forecast_value": 28.5,
            "forecast_canonical_value": 28.5,
            "source_confidence": 0.9,
            "forecast_timestamp": "2026-04-21T09:00:00Z",
        },
        market_rule={
            "market_id": "m-1",
            "market_family": "temperature_daily_max",
            "source_match_grade": "exact_station",
            "official_vs_proxy_source": "official",
            "freshness_status": "fresh",
        },
        comparison_point={
            "market_id": "m-1",
            "market_probability": 0.4,
            "fair_value": 0.75,
            "confidence_adjusted_gap": 0.4,
        },
        previous_observation_snapshot={
            "observation_value": 29.0,
            "observation_canonical_value": 29.0,
            "observed_at": "2026-04-21T09:30:00Z",
        },
        threshold_policy={
            "version": "v9",
            "threshold_value": {"threshold_cross_value": 30.0},
        },
        source_policy_status={
            "schema_version": "source_policy_status.v1",
            "overall_status": "blocked",
            "counts": {"fresh": 0, "stale": 0, "unavailable": 1},
            "problem_sources": [
                {
                    "source_name": "polymarket_clob",
                    "freshness_status": "unavailable",
                    "status_reason": "source_missing",
                }
            ],
        },
        now=datetime(2026, 4, 21, 2, 0, tzinfo=timezone.utc),
    )

    assert event["schema_version"] == "market_alert_event.v1"
    assert event["severity"] == "red"
    assert event["primary_reason"] == "threshold_cross_with_fresh_exact_station_lag+source_policy_blocked"
    assert event["recommended_operator_action"] == "review_source_policy_contract"
    assert event["signals"]["threshold_cross_value"] == 30.0
    assert event["signals"]["observation_shock"]["threshold_cross_event"] is True
    assert event["signals"]["input_mode"] == "canonical_only"
    assert event["observation_canonical_value"] == 31.0
    assert event["forecast_canonical_value"] == 28.5
    assert event["source_policy"]["overall_status"] == "blocked"
    assert event["governance_reason"] == "source_policy_blocked"

    output_path = tmp_path / "alert.jsonl"
    write_market_alert_event(output_path, event)
    assert output_path.read_text(encoding="utf-8").strip() != ""


def test_build_family_scan_report_and_write_outputs(tmp_path: Path) -> None:
    report = build_family_scan_report(
        market_rows=[
            {
                "market_id": "m-1",
                "market_family": "temperature_daily_max",
                "market_probability": 0.65,
                "model_canonical_value": 0.78,
                "spread": 0.03,
                "liquidity": 1200,
                "favored_side": "yes",
                "confidence_adjusted_gap": 0.13,
                "location_name": "Shanghai",
                "target_date": "2026-04-21",
                "variable_name": "daily_max_temperature",
            },
            {
                "market_id": "m-2",
                "market_family": "temperature_daily_max",
                "market_probability": 0.32,
                "model_canonical_value": 0.28,
                "spread": 0.06,
                "liquidity": 0,
                "favored_side": "no",
                "confidence_adjusted_gap": -0.04,
                "location_name": "Shanghai",
                "target_date": "2026-04-21",
                "variable_name": "daily_max_temperature",
            },
        ],
        comparison_history=[
            {"market_id": "m-1", "market_family": "temperature_daily_max", "market_probability": 0.55},
            {"market_id": "m-2", "market_family": "temperature_daily_max", "market_probability": 0.22},
        ],
        probability_states={
            "m-1": {"fair_value_canonical": 0.78},
            "m-2": {"fair_value_canonical": 0.28},
        },
        source_policy_status={
            "schema_version": "source_policy_status.v1",
            "overall_status": "degraded",
            "counts": {"fresh": 1, "stale": 1, "unavailable": 1},
        },
        now=datetime(2026, 4, 21, 2, 0, tzinfo=timezone.utc),
    )

    assert report["schema_version"] == "family_scan_report.v1"
    assert report["market_count"] == 2
    assert report["family_count"] == 1
    assert report["input_mode"] == "canonical_only"
    assert len(report["feature_rows"]) == 2
    assert len(report["anomaly_events"]) == 2
    assert report["feature_rows"][0]["input_mode"] == "canonical_only"
    assert report["feature_rows"][0]["anomaly_bucket"] in {"low", "medium", "high"}
    assert "feature_breakdown" in report["anomaly_events"][0]
    assert report["anomaly_events"][0]["anomaly_bucket"] in {"low", "medium", "high"}
    assert report["top_anomalies"][0]["market_id"] in {"m-1", "m-2"}
    assert report["source_policy"]["overall_status"] == "degraded"
    assert report["anomaly_events"][0]["governance_reason"] == "source_policy_degraded"
    assert report["anomaly_events"][0]["input_mode"] == "canonical_only"
    assert "market_probability" in report["anomaly_events"][0]
    assert report["signal_summary"]["price_velocity_high_count"] == 2
    assert report["signal_summary"]["edge_dislocation_high_count"] == 1
    assert report["signal_summary"]["microstructure_stress_high_count"] == 1
    assert report["family_summaries"][0]["signal_summary"]["price_velocity_high_count"] == 2

    report_path = tmp_path / "family_scan.json"
    out = write_family_scan_report(report_path, report)
    assert out.exists()
