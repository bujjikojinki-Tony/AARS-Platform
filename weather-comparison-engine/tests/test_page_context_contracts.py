from __future__ import annotations

from weather_comparison_engine.command_center import build_command_context_view
from weather_comparison_engine.market_workstation import build_market_workstation_view
from weather_comparison_engine.opportunity_board import build_opportunity_board_view
from weather_comparison_engine.operations_monitor import build_operations_monitor_view_from_files
from weather_comparison_engine.settings import (
    EVIDENCE_SCAN_SNAPSHOT_JSON,
    FAMILY_ANOMALY_SUMMARY_JSON,
    GATE_STACK_API_JSON,
    MARKET_ANOMALY_EVENTS_DIR,
    MARKET_ALERT_EVENTS_JSON,
    MARKET_UNIVERSE_SNAPSHOT_JSON,
    MARKET_WORKSTATION_OUTPUT_DIR,
    OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON,
    SCAN_QUEUE_STATUS_JSON,
    SCANNER_OPS_ALERTS_JSON,
    SCANNER_STATUS_JSON,
    SOURCE_POLICY_STATUS_JSON,
    UNIFIED_STATUS_JSON,
)


def test_operations_monitor_materializes_page_context_into_view_contract() -> None:
    base_view = build_operations_monitor_view_from_files(
        scanner_status_path=SCANNER_STATUS_JSON,
        scan_queue_status_path=SCAN_QUEUE_STATUS_JSON,
        market_universe_snapshot_path=MARKET_UNIVERSE_SNAPSHOT_JSON,
        evidence_scan_snapshot_path=EVIDENCE_SCAN_SNAPSHOT_JSON,
        opportunity_board_path=OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON,
        source_policy_status_path=SOURCE_POLICY_STATUS_JSON,
        gate_stack_api_path=GATE_STACK_API_JSON,
        unified_status_path=UNIFIED_STATUS_JSON,
        family_anomaly_summary_path=FAMILY_ANOMALY_SUMMARY_JSON,
        market_alert_events_dir=MARKET_ALERT_EVENTS_JSON.parent,
        market_anomaly_events_dir=MARKET_ANOMALY_EVENTS_DIR,
        market_workstation_dir=MARKET_WORKSTATION_OUTPUT_DIR,
        scanner_ops_alerts_path=SCANNER_OPS_ALERTS_JSON,
    )
    market_id = str(base_view["market_monitor_cards"][0]["market_id"])

    view = build_operations_monitor_view_from_files(
        page_context={
            "source_page": "operations_monitor",
            "target_page": "workstation",
            "selected_market_id": market_id,
            "selected_row_id": "row-ops-monitor",
            "entry_reason": "open_workstation",
            "entry_context": {"source_page": "operations_monitor"},
        },
        scanner_status_path=SCANNER_STATUS_JSON,
        scan_queue_status_path=SCAN_QUEUE_STATUS_JSON,
        market_universe_snapshot_path=MARKET_UNIVERSE_SNAPSHOT_JSON,
        evidence_scan_snapshot_path=EVIDENCE_SCAN_SNAPSHOT_JSON,
        opportunity_board_path=OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON,
        source_policy_status_path=SOURCE_POLICY_STATUS_JSON,
        gate_stack_api_path=GATE_STACK_API_JSON,
        unified_status_path=UNIFIED_STATUS_JSON,
        family_anomaly_summary_path=FAMILY_ANOMALY_SUMMARY_JSON,
        market_alert_events_dir=MARKET_ALERT_EVENTS_JSON.parent,
        market_anomaly_events_dir=MARKET_ANOMALY_EVENTS_DIR,
        market_workstation_dir=MARKET_WORKSTATION_OUTPUT_DIR,
        scanner_ops_alerts_path=SCANNER_OPS_ALERTS_JSON,
    )

    assert view["page_context"]["source_page"] == "operations_monitor"
    assert view["page_context"]["target_page"] == "workstation"
    assert view["page_context"]["selected_market_id"] == market_id
    assert view["view_context"]["page_context"]["selected_market_id"] == market_id
    assert view["selected_market_quick_detail"]["market_id"] == market_id


def test_opportunity_board_materializes_page_context_into_view_contract() -> None:
    payload = build_opportunity_board_view(
        latest_dashboard_rows=[
            {
                "market_id": "m1",
                "city": "Shanghai",
                "market_family": "temperature_daily_max",
                "market_question": "Will Shanghai hit 30C on Apr 22?",
                "comparison_status": "aligned",
                "source_match_grade": "exact_station",
                "official_vs_proxy_source": "official",
                "resolver_confidence": 0.92,
            }
        ],
        page_context={
            "source_page": "operations_monitor",
            "target_page": "opportunity_board",
            "selected_market_id": "m1",
            "selected_row_id": "Shanghai.temperature_daily_max",
            "entry_reason": "rank_candidates",
            "entry_context": {"source_page": "operations_monitor"},
        },
    )

    assert payload["page_context"]["source_page"] == "operations_monitor"
    assert payload["page_context"]["target_page"] == "opportunity_board"
    assert payload["page_context"]["selected_market_id"] == "m1"
    assert payload["rows"][0]["row_id"] == "Shanghai.temperature_daily_max"


def test_market_workstation_materializes_page_context_into_view_contract() -> None:
    view = build_market_workstation_view(
        selected_market_id="m1",
        page_context={
            "source_page": "opportunity_board",
            "target_page": "workstation",
            "selected_market_id": "m1",
            "selected_row_id": "Shanghai.temperature_daily_max",
            "entry_reason": "open_workstation",
            "entry_context": {
                "recommended_action": "open_workstation",
                "best_model": "ECMWF",
            },
        },
        top_parameter_view={
            "schema_version": "top_parameter_view.v2",
            "market_id": "m1",
            "market_question": "Will Shanghai hit 30C on Apr 22?",
            "market_family": "temperature_daily_max",
            "location_name": "Shanghai",
        },
        resolver_rule={"market_id": "m1"},
        comparison_row={"market_id": "m1", "comparison_status": "aligned"},
        gate_summary={"execution_gate": "blocked", "primary_block_reason": "validation coverage < 80%"},
        opportunity_context={
            "row_id": "Shanghai.temperature_daily_max",
            "selected_market_id": "m1",
            "recommended_action": "open_workstation",
            "best_model": "ECMWF",
        },
        validation_summary={"promotion_state": "shadow"},
    )

    assert view["page_context"]["source_page"] == "opportunity_board"
    assert view["page_context"]["target_page"] == "workstation"
    assert view["selected_market_id"] == "m1"
    assert view["entry_context"]["source_page"] == "opportunity_board"
    assert view["entry_context"]["target_page"] == "workstation"
    assert view["entry_context"]["selected_market_id"] == "m1"
    assert view["entry_context"]["page_context"]["entry_reason"] == "open_workstation"


def test_command_context_materializes_page_context_into_view_contract() -> None:
    view = build_command_context_view(
        selected_market_id="m1",
        page_context={
            "source_page": "workstation",
            "target_page": "command",
            "selected_market_id": "m1",
            "selected_row_id": "Shanghai.temperature_daily_max",
            "entry_reason": "send_to_command",
            "entry_context": {
                "recommended_action": "review_evidence",
                "market_question": "Will Shanghai hit 30C on Apr 22?",
            },
        },
        market_workstation_view={
            "generated_at": "2026-04-24T14:31:00Z",
            "selected_market_id": "m1",
            "entry_context": {
                "best_model": "ECMWF",
                "difficulty_label": "medium",
            },
            "buy_sell_decision_panel": {
                "decision_outcome": "review_evidence",
                "decision_reason": "Validation coverage 0.72 is below 0.80.",
                "market_implied_probability": 0.52,
                "fair_value": 0.61,
                "edge": 0.09,
            },
            "gate_advisory_panel": {
                "gate_summary": {
                    "can_execute": False,
                    "primary_block_reason": "validation coverage < 80%",
                    "execution_gate": "blocked",
                }
            },
        },
        gate_stack_summary={
            "generated_at": "2026-04-24T14:32:00Z",
            "execution_gate": "blocked",
        },
        authorization_status={
            "gateway_mode": "dry-run-only",
            "bot_authorization": "off",
            "approval_status": "none",
            "kill_switch": "safe",
        },
        pending_intent={"intent_id": "intent-1", "status": "pending"},
        dry_run_result={"status": "blocked"},
        latest_signal={"primary_reason": "validation coverage low"},
        audit_trail=[{"event_id": "evt-1", "action": "signal_detected"}],
    )

    assert view["page_context"]["source_page"] == "workstation"
    assert view["page_context"]["target_page"] == "command"
    assert view["selected_market_id"] == "m1"
    assert view["entry_context"]["selected_market_id"] == "m1"
    assert view["gate_stack_summary"]["primary_block_reason"] == "validation coverage < 80%"
    assert view["operator_decision_panel"]["research_direction"] == "review_evidence"
    assert view["operator_decision_panel"]["edge"] == 0.09
    assert any(item["action"] == "open_workstation" for item in view["available_actions"])
    assert any(item["action"] == "live_execute" for item in view["disabled_actions"])
