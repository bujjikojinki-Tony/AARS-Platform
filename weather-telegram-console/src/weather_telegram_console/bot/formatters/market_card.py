from __future__ import annotations

from weather_telegram_console.operator_messages import MANUAL_ADVISORY_AUDIT_MISSING
from weather_telegram_console.bot.formatters.top_parameter_view_card import (
    format_top_parameter_view_card,
)
from weather_telegram_console.bot.formatters.telegram_text import md_line


def format_market_card(payload: dict) -> str:
    advisory = payload.get("advisory_summary") or {}
    availability = payload.get("data_availability") or {}
    gate_stack = payload.get("compact_gate_stack") or {}
    promotion_state = payload.get("promotion_state") or gate_stack.get("promotion_state") or {}
    top_parameter_view = payload.get("top_parameter_view")
    workstation = payload.get("workstation_context") or {}
    family_anomaly_summary = payload.get("family_anomaly_summary") or workstation.get("family_anomaly_summary") or {}
    manual_status = _format_manual_status(availability, advisory)
    resolver_gate_reasons = ", ".join(
        str(item) for item in gate_stack.get("resolver_gate_reasons") or []
    ) or "-"
    latest_ticket = f"{advisory.get('latest_price', '-')} / {advisory.get('latest_size', '-')}"

    return (
        "*AARS Market Snapshot*\n"
        f"{format_top_parameter_view_card(top_parameter_view)}\n\n"
        "*Decision*\n"
        f"{md_line('Comparison Status', payload.get('comparison_status'))}\n"
        f"{md_line('Action Hint', payload.get('action_hint'))}\n"
        f"{md_line('Reason', payload.get('comparison_reason'))}\n"
        f"{md_line('Resolver Status', payload.get('rule_status'))}\n"
        f"{md_line('Promotion State', promotion_state.get('probability_mode'))}\n"
        f"{md_line('Promotion Reason', promotion_state.get('promotion_reason'))}\n"
        f"{md_line('Demotion Reason', promotion_state.get('demotion_reason'))}\n"
        f"{md_line('Market Snapshot Ref', payload.get('market_snapshot_ref'))}\n"
        f"{md_line('Forecast Snapshot Ref', payload.get('forecast_snapshot_ref'))}\n\n"
        "*Compact Gate Stack*\n"
        f"{md_line('Resolver Gate', gate_stack.get('resolver_gate'))}\n"
        f"{md_line('Probability Gate', gate_stack.get('probability_gate'))}\n"
        f"{md_line('Freshness Gate', gate_stack.get('freshness_gate'))}\n"
        f"{md_line('Authorization Gate', gate_stack.get('authorization_gate'))}\n"
        f"{md_line('Execution Gate', gate_stack.get('execution_gate'))}\n"
        f"{md_line('Resolver Reasons', resolver_gate_reasons)}\n\n"
        "*Manual Advisory*\n"
        f"{md_line('Status', manual_status)}\n"
        f"{md_line('Event Count', advisory.get('event_count', 0))}\n"
        f"{md_line('Latest Event', advisory.get('latest_event_type'))}\n"
        f"{md_line('Latest At', advisory.get('latest_created_at'))}\n"
        f"{md_line('Latest Decision', advisory.get('latest_decision'))}\n"
        f"{md_line('Latest Gate', advisory.get('latest_gate_status'))}\n"
        f"{md_line('Latest Ticket', latest_ticket)}\n"
        f"\n{_format_workstation_context(workstation)}"
    )


def _format_manual_status(availability: dict, advisory: dict) -> str:
    if advisory.get("event_count"):
        return "audit events recorded"
    if not availability.get("manual_advisory_audit_available", False):
        return MANUAL_ADVISORY_AUDIT_MISSING
    return "no advisory events for this market"


def _format_workstation_context(workstation: dict) -> str:
    alert = workstation.get("market_alert") if isinstance(workstation.get("market_alert"), dict) else {}
    anomaly = workstation.get("family_anomaly") if isinstance(workstation.get("family_anomaly"), dict) else {}
    family_anomaly_summary = (
        workstation.get("family_anomaly_summary")
        if isinstance(workstation.get("family_anomaly_summary"), dict)
        else {}
    )
    gate = workstation.get("gate_summary") if isinstance(workstation.get("gate_summary"), dict) else {}
    validation = (
        workstation.get("validation_summary")
        if isinstance(workstation.get("validation_summary"), dict)
        else {}
    )
    opportunity = (
        workstation.get("opportunity_entry")
        if isinstance(workstation.get("opportunity_entry"), dict)
        else {}
    )
    return (
        "*Single Market Workstation*\n"
        f"{md_line('Context Contract', workstation.get('schema_version'))}\n\n"
        "*Market Alert*\n"
        f"{md_line('Severity', alert.get('severity'))}\n"
        f"{md_line('Reason', alert.get('primary_reason'))}\n"
        f"{md_line('Action', alert.get('recommended_operator_action'))}\n\n"
        "*Family Anomaly*\n"
        f"{md_line('Score', anomaly.get('anomaly_score'))}\n"
        f"{md_line('Bucket', anomaly.get('anomaly_bucket'))}\n"
        f"{md_line('Reason', anomaly.get('primary_reason'))}\n\n"
        "*Advanced Anomaly Snapshot*\n"
        f"{md_line('Status', family_anomaly_summary.get('family_scan_status'))}\n"
        f"{md_line('Top Family', family_anomaly_summary.get('top_family'))}\n"
        f"{md_line('Top Score', family_anomaly_summary.get('top_score'))}\n"
        f"{md_line('Top Bucket', family_anomaly_summary.get('top_bucket'))}\n"
        f"{md_line('Signal Summary', family_anomaly_summary.get('signal_summary'))}\n\n"
        "*Gate Boundary*\n"
        f"{md_line('Execution Boundary', gate.get('execution_boundary'))}\n"
        f"{md_line('Execution Gate', gate.get('execution_gate'))}\n"
        f"{md_line('Primary Block', gate.get('primary_block_reason'))}\n"
        f"{md_line('Gate Action', gate.get('recommended_operator_action'))}\n\n"
        "*Validation / Coverage*\n"
        f"{md_line('Promotion State', validation.get('promotion_state'))}\n"
        f"{md_line('Freshness', validation.get('freshness_status'))}\n"
        f"{md_line('Freshness Reason', validation.get('freshness_reason'))}\n"
        f"{md_line('Coverage', validation.get('coverage_status'))}\n"
        f"{md_line('Labeled Ratio', validation.get('labeled_ratio'))}\n"
        f"{md_line('Calibration', validation.get('calibration_status'))}\n\n"
        "*Opportunity Entry*\n"
        f"{md_line('Row', opportunity.get('row_id'))}\n"
        f"{md_line('Opportunity', opportunity.get('opportunity_score'))}\n"
        f"{md_line('Difficulty', opportunity.get('difficulty_label'))}\n"
        f"{md_line('Action', opportunity.get('recommended_action'))}\n"
        f"{md_line('Best Model', opportunity.get('best_model'))}\n"
        f"{md_line('Source Stack', _format_list(opportunity.get('best_source_stack')))}\n"
    )


def _format_list(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if item) or "-"
    return str(value or "-")
