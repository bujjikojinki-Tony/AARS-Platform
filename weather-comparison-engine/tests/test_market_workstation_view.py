from __future__ import annotations

from weather_comparison_engine.market_workstation import build_market_workstation_view
from weather_comparison_engine.market_workstation import write_market_workstation_artifacts


def test_build_market_workstation_view_preserves_boundaries() -> None:
    view = build_market_workstation_view(
        selected_market_id="m1",
        top_parameter_view={
            "schema_version": "top_parameter_view.v2",
            "market_id": "m1",
            "market_family": "temperature_daily_max",
            "location_name": "Shanghai",
            "target_date": "2026-04-22",
            "variable_name": "daily_max_temperature",
            "canonical_unit": "celsius",
            "source_contract": {
                "settlement_source_type": "station_observation",
                "source_match_grade": "exact_station",
                "freshness_status": "fresh",
                "precision_policy_ref": "precision_policy.temperature_daily_max.v1",
            },
            "polymarket": {
                "yes_price": 0.58,
                "no_price": 0.42,
                "market_implied_probability": 0.58,
            },
            "decision": {
                "fair_value": 0.67,
                "edge": 0.09,
                "probability_mode": "shadow_calibrated_candidate",
                "execution_constraint": "dry_run_only",
            },
            "weather": {"station_id": "ZSPD"},
        },
        resolver_rule={"market_id": "m1", "band_scheme": "temperature_celsius_integer"},
        comparison_row={"market_id": "m1", "comparison_status": "aligned", "timestamp": "t1"},
        forecast_snapshot={"timestamp": "f1", "canonical_value": 28.1, "canonical_unit": "celsius", "model_band": 28},
        observation_snapshot={"observed_at": "o1", "canonical_value": 27.8, "canonical_unit": "celsius", "observation_band": 28},
        evidence_history_rows=[{"timestamp": "h1", "market_probability": 0.56, "comparison_status": "aligned"}],
        gate_summary={"gate_status": "BLOCKED", "execution_gate": "blocked", "blockers": ["manual_advisory_only"]},
        opportunity_context={
            "row_id": "shanghai.temperature_daily_max",
            "city": "Shanghai",
            "market_family": "temperature_daily_max",
            "opportunity_score": 0.82,
            "best_model": "ECMWF",
            "best_source_stack": ["ecmwf", "metar", "official_obs"],
            "source_precision_score": 0.91,
            "difficulty_label": "easy",
            "recommended_action": "open_workstation",
            "upstream_refs": {"market_ids": ["m1"]},
        },
        validation_summary={
            "promotion_state": "shadow_calibrated_candidate",
            "promotion_reason": "validation_pending",
            "freshness_status": "blocked",
            "labeled_ratio": 0.1,
            "sample_count": 40,
            "blockers": ["freshness:blocked"],
        },
        latest_alert={"severity": "amber", "primary_reason": "forecast_divergence"},
        latest_anomaly={"anomaly_score": 0.42, "primary_reason": "edge_dislocation"},
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
    assert view["selected_market_id"] == "m1"
    assert view["top_parameter_view"]["schema_version"] == "top_parameter_view.v2"
    assert view["rule_source_model_panel"]["best_model"]["best_model"] == "ECMWF"
    assert view["rule_source_model_panel"]["measurement_policy"]["canonical_unit"] == "celsius"
    assert view["gate_advisory_panel"]["gate_summary"]["can_execute"] == "no"
    assert view["gate_advisory_panel"]["dry_run_area"]["execution_boundary"] == "gate_stack_api.v1_only"
    assert view["evidence_timeline"]["schema_version"] == "evidence_timeline.v1"
    assert view["evidence_timeline"]["status"] == "ready"
    assert view["evidence_timeline"]["tracks"]["market_probability"]["point_count"] == 1
    assert view["evidence_timeline"]["tracks"]["forecast"]["latest"]["model_band"] == 28
    assert view["evidence_timeline"]["tracks"]["observation"]["latest"]["observation_band"] == 28
    marker_types = {marker["type"] for marker in view["evidence_timeline"]["tracks"]["events"]["markers"]}
    assert {"market_alert", "family_anomaly", "gate"}.issubset(marker_types)
    assert view["validation_compare_panel"]["schema_version"] == "validation_compare_panel.v1"
    assert view["validation_compare_panel"]["promotion_state"] == "shadow_calibrated_candidate"
    assert view["validation_compare_panel"]["primary_blocker"] == "freshness:blocked"
    assert view["buy_sell_decision_panel"]["schema_version"] == "buy_sell_decision_panel.v1"
    assert view["buy_sell_decision_panel"]["decision_outcome"] == "review_evidence"
    assert view["buy_sell_decision_panel"]["execution_boundary"] == "gate_stack_api.v1_only"
    assert view["opportunity_linkage_panel"]["schema_version"] == "opportunity_workstation_linkage.v1"
    assert view["opportunity_linkage_panel"]["market_refs"] == ["m1"]
    assert view["family_anomaly_summary"]["schema_version"] == "family_anomaly_summary.v1"
    assert view["family_anomaly_summary"]["top_family"] == "sea_ice_extent"
    assert view["entry_context"]["schema_version"] == "entry_context.v1"
    assert view["entry_context"]["source_page"] == "opportunity_board"
    assert view["entry_context"]["recommended_action"] == "open_workstation"


def test_build_market_workstation_view_emits_yes_research_direction_when_inputs_are_ready() -> None:
    view = build_market_workstation_view(
        selected_market_id="m2",
        top_parameter_view={
            "schema_version": "top_parameter_view.v2",
            "market_id": "m2",
            "source_contract": {
                "freshness_status": "fresh",
                "source_match_grade": "exact_station",
            },
            "polymarket": {
                "yes_price": 0.41,
                "no_price": 0.59,
                "market_implied_probability": 0.41,
            },
            "decision": {
                "fair_value": 0.53,
                "edge": 0.12,
                "probability_mode": "live_approved",
                "execution_constraint": "live_execution_allowed",
            },
        },
        gate_summary={"execution_gate": "pass", "can_execute": "yes"},
        opportunity_context={"source_precision_score": 0.88},
        validation_summary={"labeled_ratio": 0.92, "freshness_status": "fresh"},
    )

    assert view["buy_sell_decision_panel"]["decision_outcome"] == "research_buy_yes"
    assert view["buy_sell_decision_panel"]["market_implied_probability"] == 0.41
    assert view["buy_sell_decision_panel"]["fair_value"] == 0.53
    assert view["buy_sell_decision_panel"]["edge"] == 0.12


def test_write_market_workstation_artifacts(tmp_path) -> None:
    view = build_market_workstation_view(
        selected_market_id="m1",
        top_parameter_view={"schema_version": "top_parameter_view.v2", "market_id": "m1"},
        comparison_row={"market_id": "m1", "comparison_status": "aligned"},
        gate_summary={"gate_status": "BLOCKED", "execution_gate": "blocked"},
        validation_summary={"promotion_state": "shadow"},
    )

    artifacts = write_market_workstation_artifacts(
        output_dir=tmp_path,
        market_id="m1",
        view=view,
    )

    assert artifacts["workstation"].exists()
    assert artifacts["rule_source_model_panel"].exists()
    assert artifacts["evidence_timeline"].exists()
    assert artifacts["validation_compare"].exists()
    assert artifacts["gate_advisory_panel"].exists()
    assert artifacts["summary"].exists()
    assert "market_workstation_m1.json" == artifacts["workstation"].name
    assert "rule_source_model_panel_m1.json" == artifacts["rule_source_model_panel"].name
    assert "gate_advisory_panel_m1.json" == artifacts["gate_advisory_panel"].name
    assert "market_workstation_summary_m1.json" == artifacts["summary"].name
