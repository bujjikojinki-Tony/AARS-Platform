from __future__ import annotations

from weather_telegram_console.bot.formatters.telegram_text import md_line
from weather_telegram_console.bot.formatters.top_parameter_family_profiles import (
    get_family_top_parameter_profile,
)


def _build_signal_context_view(payload: dict, top_parameter_view: dict | None) -> dict:
    context = top_parameter_view if isinstance(top_parameter_view, dict) else {}
    confidence = payload.get("confidence", {}) if isinstance(payload.get("confidence"), dict) else {}
    market_family = str(
        context.get("market_family")
        or payload.get("market_family")
        or _infer_market_family(payload)
    ).strip()
    family_profile = get_family_top_parameter_profile(market_family)
    weather = context.get("weather") if isinstance(context.get("weather"), dict) else {}
    source_contract = context.get("source_contract") if isinstance(context.get("source_contract"), dict) else {}
    decision = context.get("decision") if isinstance(context.get("decision"), dict) else {}
    market_id = context.get("market_id") or payload.get("market_id") or "-"
    location_name = context.get("location_name") or payload.get("location_name") or "-"
    target_date = context.get("target_date") or payload.get("target_date") or "-"
    variable_name = context.get("variable_name") or payload.get("variable_name") or "-"
    obs_label = family_profile.get("observation_label", "Observation")
    fcst_label = family_profile.get("forecast_label", "Forecast")
    obs_value = weather.get("observation_value", payload.get("observation_value", "-"))
    fcst_value = weather.get("forecast_value", payload.get("model_value", "-"))
    model_band = weather.get("model_band", payload.get("model_band", "-"))
    source_grade = source_contract.get("source_match_grade", payload.get("source_match_grade", "-"))
    freshness = source_contract.get("freshness_status", payload.get("freshness_status", "-"))
    probability_mode = decision.get("probability_mode", payload.get("probability_mode", "-"))
    execution_constraint = decision.get("execution_constraint", payload.get("execution_constraint", "-"))
    action_hint = decision.get("recommended_operator_action", payload.get("action_hint", "review"))
    market_band = payload.get("market_band", decision.get("market_band", "-"))

    return {
        "market_id": market_id,
        "market_family": market_family or "signal_only",
        "location_name": location_name,
        "target_date": target_date,
        "variable_name": variable_name,
        "observation_label": obs_label,
        "forecast_label": fcst_label,
        "observation_value": obs_value,
        "forecast_value": fcst_value,
        "model_band": model_band,
        "market_band": market_band,
        "source_match_grade": source_grade,
        "freshness_status": freshness,
        "probability_mode": probability_mode,
        "execution_constraint": execution_constraint,
        "approval_status": payload.get("approval_status", "-"),
        "approval_expires_at": payload.get("approval_expires_at", "-"),
        "confidence_level": confidence.get("level", "-"),
        "confidence_score": confidence.get("score", "-"),
        "reasons": confidence.get("reasons", []) or [],
        "action_hint": action_hint,
    }


def _infer_market_family(payload: dict) -> str:
    market_family = str(payload.get("market_family") or "").strip().lower()
    if market_family:
        return market_family
    variable_name = str(payload.get("variable_name") or "").strip().lower()
    if "daily_max_temperature" in variable_name or "temperature_max" in variable_name:
        return "temperature_daily_max"
    if "daily_min_temperature" in variable_name or "temperature_min" in variable_name:
        return "temperature_daily_min"
    if "precip" in variable_name:
        return "precipitation_amount"
    if "wind" in variable_name:
        return "wind_speed"
    if "snow" in variable_name:
        return "snowfall_amount"
    return "signal_only"


def format_signal_card(
    payload: dict,
    approval_status: str = "未审批",
    approval_expires_at: str | None = None,
    top_parameter_view: dict | None = None,
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
    manual_ticket_text = (
        f"{manual_ticket.get('recommended_side', '-')} @ "
        f"{manual_ticket.get('limit_price', '-')} size {manual_ticket.get('size', '-')}"
    )
    confidence_text = f"{confidence.get('level', '-')} ({confidence.get('score', '-')})"
    context = _build_signal_context_view(payload, top_parameter_view)
    market_context = (
        f"{context['market_id']} | {context['market_family']} | {context['location_name']}"
    )
    weather_context = (
        f"{context['observation_label']} {context['observation_value']} | "
        f"{context['forecast_label']} {context['forecast_value']} | band {context['model_band']}"
    )
    source_context = f"{context['source_match_grade']} | {context['freshness_status']}"
    decision_context = (
        f"{context['probability_mode']} | {context['execution_constraint']} | "
        f"approval {context['approval_status']}"
    )

    return (
        "🌦 *Weather Signal Alert*\n\n"
        "*Signal Context*\n"
        f"{md_line('Market', market_context)}\n"
        f"{md_line('Weather', weather_context)}\n"
        f"{md_line('Source', source_context)}\n"
        f"{md_line('Decision', decision_context)}\n"
        f"{md_line('Action Hint', context['action_hint'])}\n\n"
        "*Signal Evidence*\n"
        f"{md_line('Signal ID', payload.get('signal_id'))}\n"
        f"{md_line('Market Band', context['market_band'])}\n"
        f"{md_line('Model Value', payload.get('model_value'))}\n"
        f"{md_line('Model Band', payload.get('model_band'))}\n"
        f"{md_line('Edge Direction', payload.get('edge_direction'))}\n"
        f"{md_line('Edge Strength', payload.get('edge_strength'))}\n\n"
        "*Signal Control*\n"
        f"{md_line('Approval Status', approval_status)}\n"
        f"{md_line('Approval Expires At', expires_text)}\n"
        f"{md_line('Execution Mode', execution_mode)}\n"
        f"{md_line('Probability Mode', probability_mode)}\n"
        f"{md_line('Execution Constraint', execution_constraint)}\n"
        f"{md_line('Manual Order Required', manual_required)}\n"
        f"{md_line('Autonomous Execution Allowed', auto_allowed)}\n"
        f"{md_line('Manual Ticket', manual_ticket_text)}\n"
        f"{md_line('Confidence', confidence_text)}\n"
        f"{md_line('Reasons', reasons_text)}\n"
        "\n_Advisory mode: BOT提醒与记录，不代表自动下单。人工如需交易，请在交易所手动确认。_\n"
    )
