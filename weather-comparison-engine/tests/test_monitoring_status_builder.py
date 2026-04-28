import json
from datetime import datetime, timezone

from typer.testing import CliRunner

from weather_comparison_engine import main as comparison_main
from weather_comparison_engine.monitoring import MonitoringStatusBuilder


def test_monitoring_status_builder_marks_stale_and_missing(tmp_path):
    market_path = tmp_path / "market.json"
    market_path.write_text(
        json.dumps({"updated_at": "2026-04-18T03:55:00+00:00"}),
        encoding="utf-8",
    )

    report = MonitoringStatusBuilder(
        now=datetime(2026, 4, 18, 4, 5, 0, tzinfo=timezone.utc)
    ).build(
        [
            {"worker": "market", "path": market_path, "stale_after_seconds": 60},
            {"worker": "forecast", "path": tmp_path / "missing.json", "stale_after_seconds": 300},
        ]
    )

    assert report["overall_status"] == "degraded"
    assert report["counts"]["stale"] == 1
    assert report["counts"]["missing"] == 1


def test_monitoring_status_builder_marks_payload_blocked(tmp_path):
    quality_path = tmp_path / "coverage.json"
    quality_path.write_text(
        json.dumps({"generated_at": "2026-04-18T03:55:00+00:00", "status": "blocked"}),
        encoding="utf-8",
    )

    report = MonitoringStatusBuilder(
        now=datetime(2026, 4, 18, 4, 0, 0, tzinfo=timezone.utc)
    ).build(
        [
            {"worker": "coverage", "path": quality_path, "stale_after_seconds": 3600},
        ]
    )

    assert report["counts"]["blocked"] == 1
    assert report["workers"][0]["status"] == "blocked"
    assert report["overall_status"] == "degraded"


def test_monitoring_status_builder_reads_overall_status(tmp_path):
    source_policy_path = tmp_path / "source_policy_status.json"
    source_policy_path.write_text(
        json.dumps(
            {
                "generated_at": "2026-04-18T03:55:00+00:00",
                "overall_status": "blocked",
                "counts": {"fresh": 1, "stale": 2, "unavailable": 1},
            }
        ),
        encoding="utf-8",
    )

    report = MonitoringStatusBuilder(
        now=datetime(2026, 4, 18, 4, 0, 0, tzinfo=timezone.utc)
    ).build(
        [
            {"worker": "source_policy_status", "path": source_policy_path, "stale_after_seconds": 3600},
        ]
    )

    assert report["workers"][0]["status"] == "blocked"
    assert report["counts"]["blocked"] == 1
    assert report["overall_status"] == "degraded"


def test_build_monitoring_status_cli_writes_report(monkeypatch, tmp_path):
    out_path = tmp_path / "monitoring_status.json"
    source_registry_path = tmp_path / "source_policy_registry.json"
    source_registry_path.write_text(
        json.dumps(
            {
                "schema_version": "source_policy_registry.v1",
                "sources": [
                    {
                        "source_name": "polymarket_clob",
                        "source_type": "market_realtime",
                        "primary_use": "market truth",
                        "trigger_mode": "websocket",
                        "selected_market_poll_interval": "1-5s",
                        "watchlist_poll_interval": "5-15s",
                        "family_scan_interval": "1-5m",
                        "write_interval": "1-5s",
                        "fresh_threshold": "30s",
                        "stale_threshold": "600s",
                        "priority_level": "critical",
                        "fallback_policy": "fallback",
                        "status": "active",
                        "version": "v1",
                    },
                    {
                        "source_name": "ecmwf",
                        "source_type": "forecast_synoptic",
                        "primary_use": "global forecast",
                        "trigger_mode": "poll",
                        "selected_market_poll_interval": "15-30m",
                        "watchlist_poll_interval": "30-60m",
                        "family_scan_interval": "60-120m",
                        "write_interval": "on_new_run",
                        "fresh_threshold": "12h",
                        "stale_threshold": "24h",
                        "priority_level": "high",
                        "fallback_policy": "fallback",
                        "status": "active",
                        "version": "v1",
                    },
                    {
                        "source_name": "resolver_registry",
                        "source_type": "rule_contract",
                        "primary_use": "market rule",
                        "trigger_mode": "event",
                        "selected_market_poll_interval": "on_select",
                        "watchlist_poll_interval": "30-60m",
                        "family_scan_interval": "60-120m",
                        "write_interval": "on_change",
                        "fresh_threshold": "6h",
                        "stale_threshold": "24h",
                        "priority_level": "high",
                        "fallback_policy": "fallback",
                        "status": "active",
                        "version": "v1",
                    },
                    {
                        "source_name": "comparison_engine",
                        "source_type": "derived_state",
                        "primary_use": "comparison rows",
                        "trigger_mode": "event",
                        "selected_market_poll_interval": "event",
                        "watchlist_poll_interval": "1-5m",
                        "family_scan_interval": "5-15m",
                        "write_interval": "on_recompute",
                        "fresh_threshold": "15m",
                        "stale_threshold": "60m",
                        "priority_level": "high",
                        "fallback_policy": "fallback",
                        "status": "active",
                        "version": "v1",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    paths = {
        "REALTIME_MARKET_JSON": tmp_path / "market.json",
        "REALTIME_FORECAST_JSON": tmp_path / "forecast.json",
        "RESOLVER_REPORT_JSON": tmp_path / "resolver.json",
        "PROBABILITY_SHADOW_REPORT_JSON": tmp_path / "probability.json",
        "LATEST_DASHBOARD_ROWS_JSON": tmp_path / "comparison.json",
        "EXECUTION_GATEWAY_PRODUCTION_READINESS_JSON": tmp_path / "gateway.json",
        "MODEL_VALIDATION_REPORT_JSON": tmp_path / "validation.json",
        "VALIDATION_FRESHNESS_STATUS_JSON": tmp_path / "validation_freshness.json",
        "LABEL_COVERAGE_REPORT_JSON": tmp_path / "label_coverage.json",
    }
    payloads = {
        "REALTIME_MARKET_JSON": {"updated_at": "2026-04-18T04:00:00+00:00"},
        "REALTIME_FORECAST_JSON": {"timestamp": "2026-04-18T03:55:00+00:00"},
        "RESOLVER_REPORT_JSON": {"generated_at": "2026-04-18T03:55:00+00:00"},
        "PROBABILITY_SHADOW_REPORT_JSON": {"generated_at": "2026-04-18T03:55:00+00:00"},
        "LATEST_DASHBOARD_ROWS_JSON": {"updated_at": "2026-04-18T03:55:00+00:00"},
        "EXECUTION_GATEWAY_PRODUCTION_READINESS_JSON": {"generated_at": "2026-04-18T03:55:00+00:00"},
        "MODEL_VALIDATION_REPORT_JSON": {"generated_at": "2026-04-18T03:55:00+00:00"},
        "VALIDATION_FRESHNESS_STATUS_JSON": {
            "generated_at": "2026-04-18T03:55:00+00:00",
            "status": "healthy",
        },
        "LABEL_COVERAGE_REPORT_JSON": {
            "generated_at": "2026-04-18T03:55:00+00:00",
            "status": "healthy",
        },
    }

    for key, path in paths.items():
        path.write_text(json.dumps(payloads[key]), encoding="utf-8")
        monkeypatch.setattr(comparison_main, key, path)

    monkeypatch.setattr(comparison_main, "MONITORING_STATUS_JSON", out_path)
    monkeypatch.setattr(comparison_main, "SOURCE_POLICY_REGISTRY_JSON", source_registry_path)
    monkeypatch.setattr(
        comparison_main,
        "MonitoringStatusBuilder",
        lambda: MonitoringStatusBuilder(
            now=datetime(2026, 4, 18, 4, 5, 0, tzinfo=timezone.utc)
        ),
    )

    result = CliRunner().invoke(comparison_main.app, ["build-monitoring-status"])

    assert result.exit_code == 0
    assert out_path.exists()
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["schema_version"] == "monitoring_status.v1"
    assert len(report["workers"]) == 10
    assert any(worker["worker"] == "source_policy_status" for worker in report["workers"])
    market_worker = next(worker for worker in report["workers"] if worker["worker"] == "market_realtime")
    assert market_worker["stale_after_seconds"] == 600
    assert market_worker["status"] == "healthy"
