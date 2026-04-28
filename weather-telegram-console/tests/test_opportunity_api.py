from __future__ import annotations

import json
from pathlib import Path

from weather_telegram_console.integrations.opportunity_api import OpportunityAPI


def test_opportunity_api_loads_board_and_filters_by_city(monkeypatch, tmp_path) -> None:
    board = tmp_path / "opportunity_board_view.json"
    family_dir = tmp_path / "family_scan_reports"
    family_dir.mkdir()
    board.write_text(
        json.dumps(
            {
                "schema_version": "opportunity_board_view.v1",
                "generated_at": "2026-04-22T00:00:00+00:00",
                "row_count": 2,
                "summary": {"city_count": 2, "family_count": 2, "top_model": "ECMWF", "top_action": "prioritize_review"},
                "rows": [
                    {"row_id": "Shanghai.station_temperature", "city": "Shanghai", "market_family": "station_temperature", "opportunity_score": 0.8, "difficulty_score": 0.3, "best_model": "ECMWF", "recommended_action": "prioritize_review"},
                    {"row_id": "Beijing.station_temperature", "city": "Beijing", "market_family": "station_temperature", "opportunity_score": 0.6, "difficulty_score": 0.5, "best_model": "ECMWF", "recommended_action": "open_workstation"},
                ],
            }
        ),
        encoding="utf-8",
    )
    (family_dir / "family_scan.json").write_text(
        json.dumps(
            {
                "schema_version": "family_scan_report.v1",
                "generated_at": "2026-04-22T01:00:00+00:00",
                "input_mode": "canonical_only",
                "family_summaries": [
                    {
                        "market_family": "sea_ice_extent",
                        "max_intervention_like_score": 0.91,
                        "signal_summary": "pv=1 edge=1 mismatch=0 stress=2 peer=1 high=2",
                    }
                ],
                "signal_summary": {
                    "price_velocity_high_count": 1,
                    "edge_dislocation_high_count": 1,
                    "evidence_mismatch_count": 0,
                    "microstructure_stress_high_count": 2,
                    "peer_outlier_count": 1,
                    "intervention_like_high_count": 2,
                },
                "anomaly_bucket_counts": {"high": 1, "medium": 0, "low": 0},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPPORTUNITY_BOARD_VIEW_JSON_PATH", str(board))
    monkeypatch.setenv("OPPORTUNITY_BOARD_CITY_DIR_PATH", str(tmp_path / "missing_city_dir"))
    monkeypatch.setenv("FAMILY_SCAN_REPORTS_DIR", str(family_dir))

    payload = OpportunityAPI().load_opportunity_board("Shanghai")

    assert payload["schema_version"] == "opportunity_board_view.v1"
    assert payload["row_count"] == 1
    assert payload["selected_city"] == "Shanghai"
    assert payload["rows"][0]["city"] == "Shanghai"
    assert payload["family_anomaly_summary"]["top_family"] == "sea_ice_extent"


def test_opportunity_api_prefers_city_payload(monkeypatch, tmp_path) -> None:
    board = tmp_path / "opportunity_board_view.json"
    family_dir = tmp_path / "family_scan_reports"
    family_dir.mkdir()
    board.write_text(
        json.dumps(
            {
                "schema_version": "opportunity_board_view.v1",
                "generated_at": "2026-04-22T00:00:00+00:00",
                "row_count": 1,
                "summary": {},
                "rows": [
                    {"row_id": "Shanghai.station_temperature", "city": "Shanghai", "market_family": "station_temperature"}
                ],
            }
        ),
        encoding="utf-8",
    )
    (family_dir / "family_scan.json").write_text(
        json.dumps(
            {
                "schema_version": "family_scan_report.v1",
                "generated_at": "2026-04-22T01:00:00+00:00",
                "input_mode": "canonical_only",
                "family_summaries": [
                    {
                        "market_family": "sea_ice_extent",
                        "max_intervention_like_score": 0.91,
                        "signal_summary": "pv=1 edge=1 mismatch=0 stress=2 peer=1 high=2",
                    }
                ],
                "signal_summary": {
                    "price_velocity_high_count": 1,
                    "edge_dislocation_high_count": 1,
                    "evidence_mismatch_count": 0,
                    "microstructure_stress_high_count": 2,
                    "peer_outlier_count": 1,
                    "intervention_like_high_count": 2,
                },
                "anomaly_bucket_counts": {"high": 1, "medium": 0, "low": 0},
            }
        ),
        encoding="utf-8",
    )
    city_dir = tmp_path / "cities"
    city_dir.mkdir()
    (city_dir / "city_opportunity_shanghai.json").write_text(
        json.dumps(
            {
                "schema_version": "city_opportunity.v1",
                "city": "Shanghai",
                "row_count": 1,
                "rows": [
                    {"row_id": "Shanghai.station_temperature", "city": "Shanghai", "market_family": "station_temperature", "best_model": "ECMWF"}
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPPORTUNITY_BOARD_VIEW_JSON_PATH", str(board))
    monkeypatch.setenv("OPPORTUNITY_BOARD_CITY_DIR_PATH", str(city_dir))
    monkeypatch.setenv("FAMILY_SCAN_REPORTS_DIR", str(family_dir))

    payload = OpportunityAPI().load_opportunity_board("Shanghai")

    assert payload["schema_version"] == "city_opportunity.v1"
    assert payload["selected_city"] == "Shanghai"
    assert payload["rows"][0]["best_model"] == "ECMWF"
    assert payload["family_anomaly_summary"]["top_bucket"] == "high"


def test_opportunity_api_prefers_phase30_artifacts(monkeypatch, tmp_path) -> None:
    board = tmp_path / "opportunity_board_view.json"
    board.write_text(
        json.dumps(
            {
                "schema_version": "opportunity_board_view.v1",
                "generated_at": "2026-04-22T00:00:00+00:00",
                "row_count": 1,
                "summary": {"city_count": 1, "family_count": 1},
                "rows": [
                    {"row_id": "Shanghai.station_temperature", "city": "Shanghai", "market_family": "station_temperature"}
                ],
            }
        ),
        encoding="utf-8",
    )
    validation_dir = tmp_path / "validation"
    anomaly_dir = tmp_path / "anomaly"
    validation_dir.mkdir()
    anomaly_dir.mkdir()
    (validation_dir / "validation_summary_all.json").write_text(
        json.dumps(
            {
                "schema_version": "validation_summary.v1",
                "generated_at": "2026-04-22T12:00:00+00:00",
                "scope_type": "family",
                "scope_id": "all",
                "validation_status": "strong",
                "validation_age": "1h",
                "label_coverage": 0.95,
                "source_coverage": 0.9,
                "normalization_consistency": 1.0,
                "family_support_level": "strong",
                "promotion_readiness": "ready",
            }
        ),
        encoding="utf-8",
    )
    (anomaly_dir / "family_anomaly_summary_sea_ice_extent.json").write_text(
        json.dumps(
            {
                "schema_version": "family_anomaly_summary.v1",
                "generated_at": "2026-04-22T12:05:00+00:00",
                "market_family": "sea_ice_extent",
                "scanned_market_count": 2,
                "high_anomaly_count": 1,
                "high_intervention_like_count": 1,
                "family_risk_summary": "moderate_family_anomaly_risk",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPPORTUNITY_BOARD_VIEW_JSON_PATH", str(board))
    monkeypatch.setenv("VALIDATION_OUTPUT_DIR", str(validation_dir))
    monkeypatch.setenv("ADVANCED_ANOMALY_OUTPUT_DIR", str(anomaly_dir))
    monkeypatch.setenv("FAMILY_SCAN_REPORTS_DIR", str(tmp_path / "missing_family_scan_reports"))
    monkeypatch.setenv("OPPORTUNITY_BOARD_CITY_DIR_PATH", str(tmp_path / "missing_city_dir"))

    payload = OpportunityAPI().load_opportunity_board()

    assert payload["validation_summary_v1"]["validation_status"] == "strong"
    assert payload["family_anomaly_summary"]["top_family"] == "sea_ice_extent"
