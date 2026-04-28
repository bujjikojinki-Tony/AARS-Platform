from __future__ import annotations

from weather_dashboard.ui.market_workstation_page import (
    build_market_workstation_view,
    find_opportunity_context,
    load_latest_market_alert,
    load_latest_market_anomaly,
)
from weather_dashboard.ui.r5_pages import build_command_context_view


def test_find_opportunity_context_prefers_market_ref() -> None:
    board = {
        "rows": [
            {
                "row_id": "miami.temperature_daily_max",
                "city": "Miami",
                "market_family": "temperature_daily_max",
                "upstream_refs": {"market_ids": ["m_other"]},
            },
            {
                "row_id": "shanghai.temperature_daily_max",
                "city": "Shanghai",
                "market_family": "temperature_daily_max",
                "best_model": "ECMWF",
                "upstream_refs": {"market_ids": ["m_focus"]},
            },
        ]
    }

    row = find_opportunity_context(
        board,
        market_id="m_focus",
        city="Miami",
        market_family="temperature_daily_max",
    )

    assert row["row_id"] == "shanghai.temperature_daily_max"
    assert row["best_model"] == "ECMWF"


def test_build_market_workstation_view_keeps_gate_boundary() -> None:
    view = build_market_workstation_view(
        selected_market_id="m_focus",
        top_parameter_view={
            "schema_version": "top_parameter_view.v2",
            "market_id": "m_focus",
            "market_family": "temperature_daily_max",
            "location_name": "Shanghai",
            "target_date": "2026-04-22",
            "variable_name": "daily_max_temperature",
            "canonical_unit": "celsius",
            "source_contract": {
                "source_match_grade": "exact_station",
                "official_vs_proxy_source": "official",
                "freshness_status": "fresh",
                "precision_policy_ref": "precision_policy.temperature_daily_max.v1",
            },
            "polymarket": {
                "market_implied_probability": 0.55,
                "yes_price": 0.55,
                "no_price": 0.45,
            },
            "decision": {
                "fair_value": 0.61,
                "edge": 0.06,
                "probability_mode": "shadow_calibrated_candidate",
            },
            "weather": {"station_id": "ZSPD"},
        },
        resolver_rule={
            "market_id": "m_focus",
            "band_scheme": "temperature_celsius_integer",
            "resolver_confidence": 0.92,
        },
        comparison_row={"market_id": "m_focus", "comparison_status": "aligned", "fair_value": 0.61},
        forecast_snapshot={
            "timestamp": "2026-04-22T00:00:00Z",
            "display_value": 27.2,
            "canonical_value": 27.2,
            "canonical_unit": "celsius",
            "model_band": 27,
        },
        observation_snapshot={
            "observed_at": "2026-04-22T01:00:00Z",
            "display_value": 26.8,
            "canonical_value": 26.8,
            "canonical_unit": "celsius",
            "observation_band": 27,
        },
        evidence_history_rows=[
            {"timestamp": "t1", "market_probability": 0.55, "comparison_status": "aligned"},
            {"timestamp": "t2", "market_probability": 0.57, "comparison_status": "aligned"},
        ],
        gate_summary={
            "gate_status": "BLOCKED",
            "execution_gate": "blocked",
            "freshness_gate": "blocked",
            "blockers": ["manual_advisory_only"],
        },
        opportunity_context={
            "row_id": "shanghai.temperature_daily_max",
            "city": "Shanghai",
            "market_family": "temperature_daily_max",
            "opportunity_score": 0.82,
            "opportunity_rank": 1,
            "best_model": "ECMWF",
            "best_source_stack": ["ecmwf", "metar", "official_obs"],
            "difficulty_score": 0.21,
            "difficulty_label": "easy",
            "recommended_action": "open_workstation",
            "source_precision_score": 0.91,
            "latest_alert_severity": "amber",
            "latest_anomaly_score": 0.44,
            "upstream_refs": {"market_ids": ["m_focus"], "alert_refs": ["a1"], "anomaly_refs": ["z1"]},
        },
        page_context={
            "schema_version": "page_context.v1",
            "source_page": "opportunity_board",
            "target_page": "workstation",
            "selected_market_id": "m_focus",
            "entry_reason": "open_workstation",
            "entry_context": {"recommended_action": "open_workstation"},
        },
        validation_summary={
            "promotion_state": "shadow_calibrated_candidate",
            "promotion_reason": "validation_pending",
            "freshness_status": "blocked",
            "coverage_status": "blocked",
            "labeled_ratio": 0.1,
            "sample_count": 40,
            "labeled_sample_count": 4,
            "canonical_ratio": 1.0,
            "source_policy_coverage": 1.0,
            "normalization_coverage": 1.0,
            "blockers": ["freshness:blocked"],
        },
        latest_family_scan_report={
            "schema_version": "family_scan_report.v1",
            "generated_at": "2026-04-22T02:30:00Z",
            "input_mode": "canonical_only",
            "family_summaries": [
                {
                    "market_family": "sea_ice_extent",
                    "max_intervention_like_score": 0.88,
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
        },
    )

    assert view["schema_version"] == "market_workstation_view.v1"
    assert view["selected_market_id"] == "m_focus"
    assert view["page_context"]["source_page"] == "opportunity_board"
    assert view["page_context"]["target_page"] == "workstation"
    assert view["page_context"]["selected_market_id"] == "m_focus"
    assert view["page_context"]["entry_context"]["recommended_action"] == "open_workstation"
    assert view["rule_source_model_panel"]["best_model"]["best_model"] == "ECMWF"
    assert view["rule_source_model_panel"]["measurement_policy"]["canonical_unit"] == "celsius"
    assert view["evidence_timeline"]["schema_version"] == "evidence_timeline.v1"
    assert view["evidence_timeline"]["status"] == "ready"
    assert view["evidence_timeline"]["tracks"]["market_probability"]["point_count"] == 2
    assert view["evidence_timeline"]["tracks"]["forecast"]["latest"]["model_band"] == 27
    assert view["evidence_timeline"]["tracks"]["observation"]["latest"]["observation_band"] == 27
    assert view["validation_compare_panel"]["schema_version"] == "validation_compare_panel.v1"
    assert view["validation_compare_panel"]["promotion_state"] == "shadow_calibrated_candidate"
    assert view["validation_compare_panel"]["primary_blocker"] == "freshness:blocked"
    assert view["family_anomaly_summary"]["schema_version"] == "family_anomaly_summary.v1"
    assert view["family_anomaly_summary"]["top_family"] == "sea_ice_extent"
    assert view["family_anomaly_summary"]["top_bucket"] == "high"
    assert view["opportunity_linkage_panel"]["schema_version"] == "opportunity_workstation_linkage.v1"
    assert view["opportunity_linkage_panel"]["recommended_action"] == "open_workstation"
    assert view["opportunity_linkage_panel"]["market_refs"] == ["m_focus"]
    assert view["gate_advisory_panel"]["gate_summary"]["can_execute"] == "no"
    assert view["gate_advisory_panel"]["dry_run_area"]["execution_boundary"] == "gate_stack_api.v1_only"
    assert view["buy_sell_decision_panel"]["schema_version"] == "buy_sell_decision_panel.v1"
    assert view["buy_sell_decision_panel"]["decision_outcome"] == "review_evidence"
    assert view["buy_sell_decision_panel"]["execution_boundary"] == "gate_stack_api.v1_only"


def test_build_command_context_view_keeps_page_context_contract() -> None:
    workstation_view = build_market_workstation_view(
        selected_market_id="m_focus",
        top_parameter_view={
            "schema_version": "top_parameter_view.v2",
            "market_id": "m_focus",
            "market_family": "temperature_daily_max",
            "location_name": "Shanghai",
            "target_date": "2026-04-22",
            "variable_name": "daily_max_temperature",
            "canonical_unit": "celsius",
            "source_contract": {
                "source_match_grade": "exact_station",
                "official_vs_proxy_source": "official",
                "freshness_status": "fresh",
                "precision_policy_ref": "precision_policy.temperature_daily_max.v1",
            },
            "polymarket": {
                "market_implied_probability": 0.52,
                "yes_price": 0.52,
                "no_price": 0.48,
            },
            "decision": {
                "fair_value": 0.61,
                "edge": 0.09,
                "probability_mode": "shadow_calibrated_candidate",
            },
            "weather": {"station_id": "ZSPD"},
        },
        resolver_rule={
            "market_id": "m_focus",
            "band_scheme": "temperature_celsius_integer",
            "resolver_confidence": 0.92,
        },
        comparison_row={"market_id": "m_focus", "comparison_status": "aligned", "fair_value": 0.61},
        gate_summary={
            "gate_status": "BLOCKED",
            "execution_gate": "blocked",
            "freshness_gate": "blocked",
            "blockers": ["manual_advisory_only"],
            "can_execute": False,
            "primary_block_reason": "Validation coverage < 80%",
        },
        opportunity_context={
            "row_id": "shanghai.temperature_daily_max",
            "city": "Shanghai",
            "market_family": "temperature_daily_max",
            "best_model": "ECMWF",
            "best_source_stack": ["ecmwf", "metar", "official_obs"],
            "difficulty_score": 0.21,
            "difficulty_label": "easy",
            "recommended_action": "open_workstation",
            "source_precision_score": 0.91,
        },
        validation_summary={
            "label_coverage": 0.723,
            "promotion_state": "shadow_calibrated_candidate",
            "promotion_reason": "validation_pending",
            "freshness_status": "blocked",
            "coverage_status": "blocked",
        },
    )

    command_view = build_command_context_view(
        workstation_view=workstation_view,
        page_context={
            "schema_version": "page_context.v1",
            "source_page": "workstation",
            "target_page": "command",
            "selected_market_id": "m_focus",
            "entry_reason": "send_to_command",
            "entry_context": {
                "recommended_action": "review_evidence",
                "best_model": "ECMWF",
                "best_source_stack": ["ecmwf", "metar", "official_obs"],
            },
        },
        bot_authorized=True,
    )

    assert command_view["schema_version"] == "command_context_view.v1"
    assert command_view["selected_market_id"] == "m_focus"
    assert command_view["page_context"]["source_page"] == "workstation"
    assert command_view["page_context"]["target_page"] == "command"
    assert command_view["page_context"]["selected_market_id"] == "m_focus"
    assert command_view["entry_context"]["recommended_action"] == "review_evidence"
    assert command_view["entry_context"]["best_model"] == "ECMWF"
    assert command_view["entry_context"]["best_source_stack"] == ["ecmwf", "metar", "official_obs"]
    assert command_view["command_context"]["current_state"] == "BLOCKED"
    assert command_view["command_context"]["research_direction"] == "review_evidence"
    assert command_view["command_context"]["edge"] == 0.09
    assert command_view["command_context"]["bot_authorized"] is True
    assert command_view["command_gate_summary"]["gate_status"] == "BLOCKED"


def test_load_latest_monitoring_context_filters_by_market(tmp_path) -> None:
    alert_dir = tmp_path / "alerts"
    anomaly_dir = tmp_path / "anomalies"
    alert_dir.mkdir()
    anomaly_dir.mkdir()
    (alert_dir / "a.json").write_text(
        '{"market_id":"m_other","severity":"green"}',
        encoding="utf-8",
    )
    (alert_dir / "b.json").write_text(
        '{"market_id":"m_focus","severity":"amber","primary_reason":"forecast_divergence"}',
        encoding="utf-8",
    )
    (anomaly_dir / "a.jsonl").write_text(
        '{"market_id":"m_other","anomaly_score":0.1}\n'
        '{"market_id":"m_focus","anomaly_score":0.7,"primary_reason":"edge_dislocation"}\n',
        encoding="utf-8",
    )

    assert load_latest_market_alert(alert_dir, "m_focus")["primary_reason"] == "forecast_divergence"
    assert load_latest_market_anomaly(anomaly_dir, "m_focus")["primary_reason"] == "edge_dislocation"
