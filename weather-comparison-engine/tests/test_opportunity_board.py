from __future__ import annotations

import json
from pathlib import Path

from weather_comparison_engine.opportunity_board import build_opportunity_board_view
from weather_comparison_engine.opportunity_board import load_opportunity_policy_bundle
from weather_comparison_engine.opportunity_board import write_opportunity_board_artifacts


def test_build_opportunity_board_view_ranks_and_explains():
    payload = build_opportunity_board_view(
        latest_dashboard_rows=[
            {
                "market_id": "m1",
                "market_question": "Will Shanghai hit 30C on Apr 22?",
                "market_family": "station_temperature",
                "location_name": "Shanghai",
                "comparison_status": "mild_divergence",
                "confidence_adjusted_gap": 0.14,
                "source_match_grade": "exact_station",
                "official_vs_proxy_source": "official",
                "resolver_confidence": 0.92,
            },
            {
                "market_id": "m2",
                "market_question": "Will Shanghai hit 31C on Apr 22?",
                "market_family": "station_temperature",
                "location_name": "Shanghai",
                "comparison_status": "aligned",
                "confidence_adjusted_gap": 0.01,
                "source_match_grade": "family_only",
                "official_vs_proxy_source": "proxy",
                "resolver_confidence": 0.61,
            },
        ],
        context={
            "opportunity_policy_bundle": load_opportunity_policy_bundle(),
            "alert_index": {
                "m1": {"event_id": "alert_1", "market_id": "m1", "severity": "amber", "generated_at": "2026-04-22T00:00:00+00:00"},
            },
            "anomaly_index": {
                "m1": {"event_id": "anomaly_1", "market_id": "m1", "anomaly_score": 0.73, "generated_at": "2026-04-22T00:00:00+00:00"},
            },
            "comparison_index": {
                "m1": {"timestamp": "2026-04-22T00:00:00+00:00"},
                "m2": {"timestamp": "2026-04-22T00:10:00+00:00"},
            },
            "gate_index": {
                "m1": {"market_id": "m1", "execution_gate": "blocked", "freshness_gate": "pass"},
                "m2": {"market_id": "m2", "execution_gate": "pass", "freshness_gate": "pass"},
            },
            "model_validation_report": {
                "best_model": "ECMWF",
                "best_source_stack": ["ecmwf", "metar", "official_obs"],
            },
        },
    )

    assert payload["schema_version"] == "opportunity_board_view.v1"
    assert payload["row_count"] == 1
    row = payload["rows"][0]
    assert row["row_id"] == "Shanghai.station_temperature"
    assert row["opportunity_rank"] == 1
    assert row["opportunity_score"] >= 0.0
    assert row["difficulty_label"] in {"easy", "medium", "hard"}
    assert row["best_model"] == "ECMWF"
    assert row["best_model_reason"]
    assert row["opportunity_policy_ref"] == "opportunity_scoring_policy.v1"
    assert row["scoring_policy_ref"] == "opportunity_scoring_policy.v1"
    assert row["difficulty_policy_ref"] == "difficulty_scoring_policy.v1"
    assert row["model_recommendation_policy_ref"] == "model_recommendation_policy.v1"
    assert row["action_mapping_policy_ref"] == "action_mapping_policy.v1"
    assert row["freshness_mapping_policy_ref"] == "freshness_mapping_policy.v1"
    assert row["source_precision_policy_ref"] == "source_precision_policy.v1"
    assert row["recommended_action"] in {"review_gate_block", "prioritize_review", "open_workstation", "review_hard_market"}
    assert row["upstream_refs"]["market_ids"] == ["m1", "m2"]
    assert payload["summary"]["city_count"] == 1
    assert payload["summary"]["family_count"] == 1
    assert payload["explanations"]["Shanghai.station_temperature"]["row_id"] == "Shanghai.station_temperature"
    assert payload["explanations"]["Shanghai.station_temperature"]["recommended_action_reason"]
    assert payload["explanations"]["Shanghai.station_temperature"]["policy_refs"]["opportunity_policy_ref"] == "opportunity_scoring_policy.v1"
    assert payload["explanations"]["Shanghai.station_temperature"]["policy_refs"]["scoring_policy_ref"] == "opportunity_scoring_policy.v1"
    assert payload["feature_rows"][0]["row_id"] == "Shanghai.station_temperature"


def test_write_opportunity_board_artifacts_emits_city_files(tmp_path):
    payload = build_opportunity_board_view(
        latest_dashboard_rows=[
            {
                "market_id": "m1",
                "market_question": "Will Shanghai hit 30C on Apr 22?",
                "market_family": "station_temperature",
                "location_name": "Shanghai",
                "comparison_status": "mild_divergence",
                "confidence_adjusted_gap": 0.14,
                "source_match_grade": "exact_station",
                "official_vs_proxy_source": "official",
                "resolver_confidence": 0.92,
            }
        ]
    )
    artifacts = write_opportunity_board_artifacts(
        board_path=tmp_path / "opportunity_board_view.json",
        explanation_path=tmp_path / "opportunity_board_explanations.json",
        feature_rows_path=tmp_path / "opportunity_board_feature_rows.json",
        city_dir=tmp_path / "city",
        payload=payload,
        summary_path=tmp_path / "opportunity_board" / "opportunity_board_summary.json",
        canonical_board_path=tmp_path / "opportunity_board" / "opportunity_board_view.json",
        canonical_explanation_path=tmp_path / "opportunity_board" / "opportunity_explanations.json",
        canonical_feature_rows_path=tmp_path / "opportunity_board" / "opportunity_feature_rows.json",
    )

    assert artifacts["board"].exists()
    assert artifacts["explanations"].exists()
    assert artifacts["feature_rows"].exists()
    assert artifacts["summary"].exists()
    assert artifacts["canonical_board"].exists()
    assert artifacts["canonical_explanations"].exists()
    assert artifacts["canonical_feature_rows"].exists()
    assert any(path.name.startswith("city_opportunity_") for path in artifacts["city_files"].values())
    summary = json.loads(artifacts["summary"].read_text(encoding="utf-8"))
    assert summary["schema_version"] == "opportunity_board_summary.v1"
    assert summary["total_rows"] == 1


def test_seed_list_bootstraps_opportunity_rows_without_live_market_truth():
    payload = build_opportunity_board_view(
        latest_dashboard_rows=[],
        context={
            "opportunity_policy_bundle": load_opportunity_policy_bundle(),
            "opportunity_seed_list": {
                "schema_version": "opportunity_seed_list.v1",
                "rows": [
                    {
                        "seed_id": "miami.temperature_daily_max",
                        "city": "Miami",
                        "country": "US",
                        "market_family": "temperature_daily_max",
                        "initial_edge_label": 4,
                        "initial_difficulty_label": "medium",
                        "initial_best_model": "NOAA",
                        "initial_best_source_stack": ["hrrr", "metar", "official_obs"],
                        "source_origin": "image_2_manual_research",
                        "manual_confidence": "medium",
                        "seed_status": "active",
                        "superseded_by_system_score": False,
                    }
                ],
            }
        },
    )

    assert payload["row_count"] == 1
    row = payload["rows"][0]
    assert row["row_id"] == "Miami.temperature_daily_max"
    assert row["seeded_from_manual_research"] is True
    assert row["recommended_action"] == "watch_seed"
    assert row["best_model"] == "NOAA"
    assert row["upstream_refs"]["market_ids"] == []
    assert payload["seed_summary"]["seeded_row_count"] == 1


def test_seed_list_does_not_duplicate_live_city_family_rows():
    payload = build_opportunity_board_view(
        latest_dashboard_rows=[
            {
                "market_id": "m_live",
                "city": "Miami",
                "market_family": "temperature_daily_max",
                "comparison_status": "aligned",
            }
        ],
        context={
            "opportunity_seed_list": {
                "schema_version": "opportunity_seed_list.v1",
                "rows": [
                    {
                        "seed_id": "miami.temperature_daily_max",
                        "city": "Miami",
                        "market_family": "temperature_daily_max",
                        "seed_status": "active",
                    }
                ],
            }
        },
    )

    assert payload["row_count"] == 1
    assert payload["rows"][0]["seeded_from_manual_research"] is False
    assert payload["rows"][0]["upstream_refs"]["market_ids"] == ["m_live"]


def test_source_precision_policy_uses_combination_mapping():
    payload = build_opportunity_board_view(
        latest_dashboard_rows=[
            {
                "market_id": "m_exact_proxy",
                "city": "Miami",
                "market_family": "temperature_daily_max",
                "comparison_status": "aligned",
                "source_match_grade": "exact_station",
                "official_vs_proxy_source": "proxy",
                "resolver_confidence": 1.0,
            }
        ],
        context={"opportunity_policy_bundle": load_opportunity_policy_bundle()},
    )

    row = payload["rows"][0]
    assert row["source_precision_score"] == 0.8
    assert row["opportunity_components"]["source_precision_component"] == 0.8
