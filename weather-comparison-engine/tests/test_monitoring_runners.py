from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from weather_comparison_engine.monitoring_layer.runners import (
    run_family_anomaly_scan_once,
    run_observation_alert_once,
)


def test_run_observation_alert_once_writes_event(tmp_path: Path) -> None:
    result = run_observation_alert_once(
        market_row={
            "market_id": "m-1",
            "market_family": "temperature_daily_max",
            "market_probability": 0.62,
            "fair_value": 0.71,
            "market_band": "30",
        },
        forecast_snapshot={
            "market_id": "m-1",
            "forecast_value": 29.2,
            "forecast_canonical_value": 29.2,
            "source_confidence": 0.9,
        },
        resolver_rule={
            "market_id": "m-1",
            "market_family": "temperature_daily_max",
            "source_match_grade": "exact_station",
            "official_vs_proxy_source": "official",
            "freshness_status": "fresh",
        },
        observation_snapshot={
            "market_id": "m-1",
            "observation_value": 31.1,
            "observation_canonical_value": 31.1,
            "observed_at": "2026-04-21T10:00:00Z",
            "source_match_grade": "exact_station",
        },
        previous_observation_snapshot={
            "observation_value": 29.0,
            "observation_canonical_value": 29.0,
            "observed_at": "2026-04-21T09:30:00Z",
        },
        threshold_policy={"version": "v2", "threshold_value": {"threshold_cross_value": 30.0}},
        source_policy_status={
            "schema_version": "source_policy_status.v1",
            "overall_status": "blocked",
            "counts": {"fresh": 0, "stale": 0, "unavailable": 1},
        },
        market_alert_events_dir=tmp_path,
        now=datetime(2026, 4, 21, 2, 0, tzinfo=timezone.utc),
    )

    output_path = Path(result["output_path"])
    assert output_path.exists()
    assert result["event"]["schema_version"] == "market_alert_event.v1"
    assert result["event"]["signals"]["observation_shock"]["threshold_cross_value"] == 30.0
    assert result["event"]["signals"]["input_mode"] == "canonical_only"
    assert result["event"]["observation_canonical_value"] == 31.1
    assert result["event"]["governance_reason"] == "source_policy_blocked"


def test_run_family_anomaly_scan_once_writes_report(tmp_path: Path) -> None:
    result = run_family_anomaly_scan_once(
        market_rows=[
            {
                "market_id": "m-1",
                "market_family": "temperature_daily_max",
                "market_probability": 0.62,
                "fair_value": 0.74,
                "spread": 0.03,
                "liquidity": 500,
                "confidence_adjusted_gap": 0.12,
            }
        ],
        comparison_history=[
            {"market_id": "m-1", "market_family": "temperature_daily_max", "market_probability": 0.53}
        ],
        probability_states={"m-1": {"fair_value": 0.74}},
        source_policy_status={
            "schema_version": "source_policy_status.v1",
            "overall_status": "degraded",
            "counts": {"fresh": 1, "stale": 1, "unavailable": 1},
        },
        family_scan_reports_dir=tmp_path,
        market_anomaly_events_dir=tmp_path,
        now=datetime(2026, 4, 21, 2, 0, tzinfo=timezone.utc),
    )

    report_path = Path(result["report_path"])
    anomaly_events_path = Path(result["anomaly_events_path"])
    assert report_path.exists()
    assert anomaly_events_path.exists()
    assert result["report"]["schema_version"] == "family_scan_report.v1"
    assert result["family_count"] == 1
    assert result["report"]["input_mode"] == "canonical_only"
    assert result["report"]["source_policy"]["overall_status"] == "degraded"
    assert result["report"]["anomaly_events"][0]["governance_reason"] == "source_policy_degraded"
    assert result["report"]["anomaly_events"][0]["input_mode"] == "canonical_only"
