from __future__ import annotations

import streamlit as st

from weather_dashboard.ui.compact_panel import sanitize_text
from weather_dashboard.ui.field_dictionary import field_label


def _fmt(value: object) -> str:
    if value is None or value == "":
        return "-"
    return str(value)


def _fmt_float(value: object, digits: int = 2) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def _tone(value: object) -> str:
    text = str(value or "").lower()
    if text in {"ready", "pass", "aligned", "within_limit", "true", "ok"}:
        return "ok"
    if text in {"blocked", "false", "over_limit", "stale", "degraded"}:
        return "block"
    if text in {"warning", "near_limit", "manual_advisory_only", "dry_run_only"}:
        return "warn"
    return "neutral"


def render_command_metric_cards(
    *,
    focus_summary: dict,
    account_summary: dict | None,
    operator_context_summary: dict | None,
) -> None:
    blockers = focus_summary.get("block_reasons") or []
    first_blocker = str(blockers[0]) if blockers else "none"
    account = account_summary or {}
    context = operator_context_summary or {}
    cards = [
        {
            "title": "Execution",
            "value": _fmt(focus_summary.get("gate_status")),
            "tone": _tone(focus_summary.get("gate_status")),
            "rows": [
                (field_label("execution_gate"), _fmt(focus_summary.get("execution_gate"))),
                (field_label("authorization_gate"), _fmt(focus_summary.get("authorization_gate"))),
                (field_label("primary_blocker"), first_blocker),
            ],
        },
        {
            "title": "Probability",
            "value": _fmt(focus_summary.get("probability_mode")),
            "tone": _tone(focus_summary.get("execution_constraint")),
            "rows": [
                (field_label("execution_constraint"), _fmt(focus_summary.get("execution_constraint"))),
                (field_label("edge"), _fmt(focus_summary.get("edge"))),
                (field_label("market_probability"), _fmt(focus_summary.get("market_probability"))),
            ],
        },
        {
            "title": "Evidence",
            "value": _fmt(focus_summary.get("comparison_status")),
            "tone": _tone(focus_summary.get("comparison_status")),
            "rows": [
                (field_label("confidence_adjusted_gap"), _fmt(focus_summary.get("confidence_adjusted_gap"))),
                (field_label("resolver_gate"), _fmt(focus_summary.get("resolver_gate"))),
                (field_label("freshness_gate"), _fmt(focus_summary.get("freshness_gate"))),
            ],
        },
        {
            "title": "Account",
            "value": _fmt(account.get("exposure_limit_status") or "unknown"),
            "tone": _tone(account.get("exposure_limit_status")),
            "rows": [
                (field_label("market_notional"), _fmt_money(account.get("market_notional"), account.get("balance_currency"))),
                (field_label("market_limit_usage"), _fmt_percent(account.get("market_limit_usage"))),
                (field_label("total_limit_usage"), _fmt_percent(account.get("total_limit_usage"))),
            ],
        },
        {
            "title": "Telegram",
            "value": _fmt(context.get("market_id") or focus_summary.get("market_id")),
            "tone": "neutral",
            "rows": [
                (field_label("selection_source"), _fmt(context.get("selection_source"))),
                (field_label("action_hint"), _fmt(context.get("action_hint") or focus_summary.get("recommended_operator_action"))),
                (field_label("generated_at"), _fmt(context.get("generated_at"))),
            ],
        },
    ]

    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            with st.container(border=True):
                st.caption(str(card["title"]).upper())
                st.metric(label="Status", value=str(card["value"]))
                for label, value in card["rows"]:
                    st.markdown(f"**{sanitize_text(label)}:** `{sanitize_text(value)}`")


def _fmt_money(value: object, currency: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "-"
    suffix = str(currency or "").strip()
    return f"{numeric:.2f} {suffix}".strip()


def _fmt_percent(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "-"
