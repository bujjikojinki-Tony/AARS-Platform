from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from weather_comparison_engine.monitoring_layer.alerting import route_market_alert_events
from weather_comparison_engine.monitoring_layer.market_scanner import (
    build_evidence_scan_snapshot,
    build_market_universe_snapshot,
    build_scan_status,
)


def test_market_universe_snapshot_merges_seed_board_and_watchlist(tmp_path: Path) -> None:
    seed_path = tmp_path / "opportunity_seed_list.json"
    board_path = tmp_path / "opportunity_board_view.json"
    watchlist_path = tmp_path / "watchlist.json"
    realtime_path = tmp_path / "market_realtime.json"
    seed_path.write_text(
        json.dumps(
            {
                "schema_version": "opportunity_seed_list.v1",
                "rows": [
                    {
                        "seed_id": "m-1",
                        "market_id": "m-1",
                        "city": "Shanghai",
                        "market_family": "temperature_daily_max",
                        "scan_priority": "high",
                        "liquidity_score": 0.9,
                        "spread": 0.02,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    board_path.write_text(
        json.dumps(
            {
                "schema_version": "opportunity_board_view.v1",
                "rows": [
                    {
                        "row_id": "m-2",
                        "market_id": "m-2",
                        "city": "Tokyo",
                        "market_family": "wind_speed",
                        "scan_priority": "critical",
                        "liquidity_score": 0.7,
                        "spread": 0.04,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    watchlist_path.write_text(
        json.dumps({"rows": [{"market_id": "m-3", "city": "Miami", "market_family": "temperature_daily_max"}]}, ensure_ascii=False),
        encoding="utf-8",
    )
    realtime_path.write_text(
        json.dumps({"markets": [{"market_id": "m-4", "city": "Seoul", "market_family": "temperature_daily_max"}]}, ensure_ascii=False),
        encoding="utf-8",
    )

    snapshot = build_market_universe_snapshot(
        opportunity_seed_path=seed_path,
        opportunity_board_path=board_path,
        latest_dashboard_rows_path=None,
        market_realtime_path=realtime_path,
        watchlist_path=watchlist_path,
        now=datetime(2026, 4, 21, 10, 0, tzinfo=timezone.utc),
    )

    assert snapshot["schema_version"] == "market_universe_snapshot.v1"
    assert snapshot["market_count"] == 4
    market_ids = {market["market_id"] for market in snapshot["markets"]}
    assert market_ids == {"m-1", "m-2", "m-3", "m-4"}
    seed_market = next(market for market in snapshot["markets"] if market["market_id"] == "m-1")
    assert seed_market["seeded_from_opportunity_seed"] is True
    assert "seed" in seed_market["upstream_refs"]["source_refs"]


def test_evidence_scan_and_status_reflect_freshness(tmp_path: Path) -> None:
    universe = {
        "schema_version": "market_universe_snapshot.v1",
        "generated_at": "2026-04-21T10:00:00+00:00",
        "market_count": 1,
        "markets": [
            {
                "market_id": "m-1",
                "market_family": "temperature_daily_max",
                "city": "Shanghai",
                "freshness_status": "fresh",
                "best_model": "ECMWF",
                "best_source_stack": ["ecmwf", "metar"],
            }
        ],
    }
    alert_dir = tmp_path / "alerts"
    anomaly_dir = tmp_path / "anomalies"
    alert_dir.mkdir()
    anomaly_dir.mkdir()
    (alert_dir / "alert.json").write_text(
        json.dumps(
            {
                "market_id": "m-1",
                "severity": "amber",
                "alert_score": 0.6,
                "source_match_grade": "exact_station",
                "freshness_status": "fresh",
                "contract_refs": {
                    "forecast_snapshot_ref": "forecast-1",
                    "observation_snapshot_ref": "observation-1",
                    "comparison_point_ref": "comparison-1",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (anomaly_dir / "anomaly.jsonl").write_text(
        json.dumps({"market_id": "m-1", "anomaly_score": 0.4, "primary_reason": "edge_dislocation"}) + "\n",
        encoding="utf-8",
    )

    evidence = build_evidence_scan_snapshot(
        market_universe_snapshot=universe,
        market_alert_events_dir=alert_dir,
        market_anomaly_events_dir=anomaly_dir,
        now=datetime(2026, 4, 21, 10, 5, tzinfo=timezone.utc),
    )
    assert evidence["schema_version"] == "evidence_scan_snapshot.v1"
    assert evidence["market_count"] == 1
    assert evidence["rows"][0]["scan_status"] == "healthy"
    assert evidence["rows"][0]["source_precision_score"] > 0
    assert evidence["rows"][0]["forecast_snapshot_ref"] == "forecast-1"

    status = build_scan_status(
        market_universe_snapshot=universe,
        evidence_scan_snapshot=evidence,
        alert_events=[{"market_id": "m-1", "severity": "amber"}],
        now=datetime(2026, 4, 21, 10, 6, tzinfo=timezone.utc),
    )
    assert status["schema_version"] == "scanner_status.v1"
    assert status["total_markets"] == 1
    assert status["scanned_markets"] == 1
    assert status["alert_markets"] == 1


def test_alert_router_dedupes_same_event(tmp_path: Path) -> None:
    output_path = tmp_path / "market_alert_events.json"
    queue_status_path = tmp_path / "alert_queue_status.json"
    event = {
        "market_id": "m-1",
        "event_type": "observation_alert",
        "primary_reason": "edge_dislocation",
        "severity": "amber",
    }
    result = route_market_alert_events(
        events=[event, event],
        output_path=output_path,
        queue_status_path=queue_status_path,
        now=datetime(2026, 4, 21, 10, 10, tzinfo=timezone.utc),
    )

    assert len(result["accepted"]) == 1
    assert len(result["suppressed"]) == 1
    assert output_path.exists()
    assert queue_status_path.exists()
