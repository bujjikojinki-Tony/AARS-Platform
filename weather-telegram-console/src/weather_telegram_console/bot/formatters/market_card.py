from __future__ import annotations

from weather_telegram_console.operator_messages import MANUAL_ADVISORY_AUDIT_MISSING


def format_market_card(payload: dict) -> str:
    advisory = payload.get("advisory_summary") or {}
    availability = payload.get("data_availability") or {}
    gate_stack = payload.get("compact_gate_stack") or {}
    promotion_state = payload.get("promotion_state") or gate_stack.get("promotion_state") or {}
    manual_status = _format_manual_status(availability, advisory)
    resolver_gate_reasons = ", ".join(
        str(item) for item in gate_stack.get("resolver_gate_reasons") or []
    ) or "-"

    return (
        "*AARS Market Snapshot*\n"
        f"*Market ID:* `{payload.get('market_id', '-')}`\n"
        f"*Question:* {payload.get('market_question', '-')}\n"
        f"*Location:* {payload.get('location_name', '-')}\n"
        f"*Target Date:* {payload.get('target_date', '-')}\n"
        f"*Variable:* {payload.get('variable_name', '-')}\n\n"
        "*Market Pricing*\n"
        f"*Yes Price:* `{payload.get('yes_price', '-')}`\n"
        f"*No Price:* `{payload.get('no_price', '-')}`\n"
        f"*Market Probability:* `{payload.get('market_probability', '-')}`\n"
        f"*Market Band:* `{payload.get('market_band', '-')}`\n\n"
        "*Model View*\n"
        f"*Model Value:* `{payload.get('model_value', '-')}`\n"
        f"*Model Band:* `{payload.get('model_band', '-')}`\n"
        f"*Confidence Score:* `{payload.get('confidence_score', '-')}`\n"
        f"*Adj Gap:* `{payload.get('confidence_adjusted_gap', '-')}`\n\n"
        "*Decision*\n"
        f"*Comparison Status:* `{payload.get('comparison_status', '-')}`\n"
        f"*Action Hint:* `{payload.get('action_hint', '-')}`\n"
        f"*Reason:* {payload.get('comparison_reason', '-')}\n"
        f"*Resolver Status:* `{payload.get('rule_status', '-')}`\n"
        f"*Promotion State:* `{promotion_state.get('probability_mode', '-')}`\n"
        f"*Promotion Reason:* `{promotion_state.get('promotion_reason', '-')}`\n"
        f"*Demotion Reason:* `{promotion_state.get('demotion_reason', '-')}`\n"
        f"*Market Snapshot Ref:* `{payload.get('market_snapshot_ref', '-')}`\n"
        f"*Forecast Snapshot Ref:* `{payload.get('forecast_snapshot_ref', '-')}`\n\n"
        "*Compact Gate Stack*\n"
        f"*Resolver Gate:* `{gate_stack.get('resolver_gate', '-')}`\n"
        f"*Probability Gate:* `{gate_stack.get('probability_gate', '-')}`\n"
        f"*Freshness Gate:* `{gate_stack.get('freshness_gate', '-')}`\n"
        f"*Authorization Gate:* `{gate_stack.get('authorization_gate', '-')}`\n"
        f"*Execution Gate:* `{gate_stack.get('execution_gate', '-')}`\n"
        f"*Resolver Reasons:* `{resolver_gate_reasons}`\n\n"
        "*Manual Advisory*\n"
        f"*Status:* {manual_status}\n"
        f"*Event Count:* `{advisory.get('event_count', 0)}`\n"
        f"*Latest Event:* `{advisory.get('latest_event_type', '-')}`\n"
        f"*Latest At:* `{advisory.get('latest_created_at', '-')}`\n"
        f"*Latest Decision:* `{advisory.get('latest_decision', '-')}`\n"
        f"*Latest Gate:* `{advisory.get('latest_gate_status', '-')}`\n"
        f"*Latest Ticket:* `{advisory.get('latest_price', '-')}` / `{advisory.get('latest_size', '-')}`\n"
    )


def _format_manual_status(availability: dict, advisory: dict) -> str:
    if advisory.get("event_count"):
        return "audit events recorded"
    if not availability.get("manual_advisory_audit_available", False):
        return MANUAL_ADVISORY_AUDIT_MISSING
    return "no advisory events for this market"
