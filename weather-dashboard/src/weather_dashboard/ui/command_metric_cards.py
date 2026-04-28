from __future__ import annotations

import streamlit as st

from weather_dashboard.ui.compact_panel import sanitize_text, semantic_tone, semantic_value_html
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

    st.markdown(
        """
        <style>
        .command-metric-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.32rem;
            margin-top: 0.22rem;
        }
        .command-metric-card {
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 12px;
            background: linear-gradient(180deg, rgba(16,20,26,0.98), rgba(12,15,20,0.98));
            padding: 0.42rem 0.48rem;
        }
        .command-metric-card__title {
            color: #9aa3ad;
            font-family: "SF Mono", "Menlo", monospace;
            font-size: 0.58rem;
            font-weight: 900;
            letter-spacing: 0.10em;
            text-transform: uppercase;
        }
        .command-metric-card__status {
            margin-top: 0.12rem;
            color: #f7fbff;
            font-family: "Avenir Next Condensed", "DIN Condensed", "Trebuchet MS", sans-serif;
            font-size: 1.02rem;
            font-weight: 950;
            line-height: 1.06;
        }
        .command-metric-card__rows {
            margin-top: 0.26rem;
            display: grid;
            gap: 0.16rem;
        }
        .command-metric-card__row {
            display: flex;
            justify-content: space-between;
            gap: 0.32rem;
            align-items: baseline;
            border-top: 1px solid rgba(255,255,255,0.08);
            padding-top: 0.14rem;
        }
        .command-metric-card__label {
            color: #9aa3ad;
            font-size: 0.56rem;
            font-weight: 850;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .command-metric-card__value {
            color: #f7fbff;
            font-size: 0.72rem;
            font-weight: 850;
            font-variant-numeric: tabular-nums;
            text-align: right;
        }
        @media (max-width: 1100px) {
            .command-metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            tone = semantic_tone(card["title"], card["value"])
            rows_html = "\n".join(
                f"""
                <div class="command-metric-card__row">
                  <div class="command-metric-card__label">{sanitize_text(label)}</div>
                  <div class="command-metric-card__value">{semantic_value_html(label, value)}</div>
                </div>
                """
                for label, value in card["rows"]
            )
            st.markdown(
                f"""
                <div class="command-metric-card command-metric-card--{tone}">
                  <div class="command-metric-card__title">{sanitize_text(card["title"])}</div>
                  <div class="command-metric-card__status">{semantic_value_html(card["title"], card["value"], metric=True)}</div>
                  <div class="command-metric-card__rows">
                    {rows_html}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


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
