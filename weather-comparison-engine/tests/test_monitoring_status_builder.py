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


def test_build_monitoring_status_cli_writes_report(monkeypatch, tmp_path):
    out_path = tmp_path / "monitoring_status.json"
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
        "REALTIME_MARKET_JSON": {"updated_at": "2026-04-18T03:55:00+00:00"},
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

    result = CliRunner().invoke(comparison_main.app, ["build-monitoring-status"])

    assert result.exit_code == 0
    assert out_path.exists()
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["schema_version"] == "monitoring_status.v1"
    assert len(report["workers"]) == 9
