from __future__ import annotations

from pathlib import Path

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


def test_build_operations_monitor_view_from_files_assembles_homepage_contract() -> None:
    view = build_operations_monitor_view_from_files(
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

    assert view["schema_version"] == "operations_monitor_view.v1"
    assert view["global_summary"]["markets_scanned"] == 18
    assert view["global_summary"]["focus_markets_count"] >= 1
    assert view["global_summary"]["ops_alert_count"] >= 0
    assert len(view["market_monitor_cards"]) == 18
    assert view["focus_markets"]
    assert view["system_health"]["scanner_health"]["status"] in {"healthy", "warning", "degraded"}
    assert view["selected_market_quick_detail"]["schema_version"] == "selected_market_quick_detail.v1"
    assert "selected_market_id" in view["view_context"]
    assert "scanner_status_ref" in view["upstream_refs"]


def test_build_operations_monitor_view_includes_selected_market_workstation_detail() -> None:
    view = build_operations_monitor_view_from_files(
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

    selected = view["selected_market_quick_detail"]
    assert "top_parameter_summary" in selected
    assert "gate_advisory_panel" in selected
    assert "recommended_operator_action" in selected
