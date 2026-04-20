from __future__ import annotations


def format_signal_card(
    payload: dict,
    approval_status: str = "未审批",
    approval_expires_at: str | None = None,
) -> str:
    confidence = payload.get("confidence", {})
    reasons = confidence.get("reasons", [])
    reasons_text = ", ".join(reasons) if reasons else "-"
    expires_text = approval_expires_at or "-"
    manual_ticket = payload.get("manual_trade_ticket") or {}
    execution_mode = payload.get("execution_mode") or "-"
    probability_mode = payload.get("probability_mode") or "-"
    execution_constraint = payload.get("execution_constraint") or "-"
    manual_required = payload.get("manual_order_required")
    auto_allowed = payload.get("autonomous_execution_allowed")

    return (
        "🌦 *Weather Signal Alert*\n\n"
        f"*Market ID:* `{payload.get('market_id', '-')}`\n"
        f"*Location:* {payload.get('location_name', '-')}\n"
        f"*Target Date:* {payload.get('target_date', '-')}\n"
        f"*Variable:* {payload.get('variable_name', '-')}\n\n"
        f"*Model Value:* {payload.get('model_value', '-')}\n"
        f"*Model Band:* {payload.get('model_band', '-')}\n"
        f"*Market Band:* {payload.get('market_band', '-')}\n"
        f"*Edge Direction:* {payload.get('edge_direction', '-')}\n"
        f"*Edge Strength:* {payload.get('edge_strength', '-')}\n\n"
        f"*Approval Status:* `{approval_status}`\n"
        f"*Approval Expires At:* `{expires_text}`\n"
        f"*Execution Mode:* `{execution_mode}`\n"
        f"*Probability Mode:* `{probability_mode}`\n"
        f"*Execution Constraint:* `{execution_constraint}`\n"
        f"*Manual Order Required:* `{manual_required}`\n"
        f"*Autonomous Execution Allowed:* `{auto_allowed}`\n"
        f"*Manual Ticket:* {manual_ticket.get('recommended_side', '-')} "
        f"@ {manual_ticket.get('limit_price', '-')} "
        f"size {manual_ticket.get('size', '-')}\n"
        f"*Confidence:* {confidence.get('level', '-')} ({confidence.get('score', '-')})\n"
        f"*Reasons:* {reasons_text}\n"
        f"*Action Hint:* {payload.get('action_hint', '-')}\n"
        "\n_Advisory mode: BOT提醒与记录，不代表自动下单。人工如需交易，请在交易所手动确认。_\n"
    )
