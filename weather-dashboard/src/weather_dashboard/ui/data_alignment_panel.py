from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from weather_dashboard.ui.compact_panel import render_compact_note, render_panel_title


def build_data_alignment_audit(
    *,
    selected_market_snapshot: dict | None,
    activated_market_snapshot: dict | None,
    forecast_snapshot: dict | None,
    resolver_rule: dict | None,
    probability_state: dict | None,
    comparison_row: dict | None,
) -> dict[str, Any]:
    selected_market_id = _market_id(selected_market_snapshot)
    checks = [
        _selected_check(selected_market_snapshot),
        _activated_input_check(selected_market_id, activated_market_snapshot),
        _forecast_check(selected_market_id, forecast_snapshot),
        _resolver_check(selected_market_id, resolver_rule),
        _probability_check(selected_market_id, probability_state),
        _comparison_check(selected_market_id, comparison_row),
    ]

    return {
        "selected_market_id": selected_market_id,
        "selected_question": _value(selected_market_snapshot, "market_question"),
        "activated_market_id": _market_id(activated_market_snapshot),
        "forecast_market_id": _market_id(forecast_snapshot),
        "resolver_market_id": _market_id(resolver_rule),
        "probability_market_id": _market_id(probability_state),
        "comparison_market_id": _market_id(comparison_row),
        "checks": checks,
        "ready_for_bot": all(check["level"] == "ok" for check in checks[1:]),
    }


def render_data_alignment_panel(
    *,
    selected_market_snapshot: dict | None,
    activated_market_snapshot: dict | None,
    forecast_snapshot: dict | None,
    resolver_rule: dict | None,
    probability_state: dict | None,
    comparison_row: dict | None,
    validation_freshness_status: dict | None = None,
    label_coverage_report: dict | None = None,
    bot_authorized: bool,
) -> None:
    render_panel_title("Data Alignment Audit")

    audit = build_data_alignment_audit(
        selected_market_snapshot=selected_market_snapshot,
        activated_market_snapshot=activated_market_snapshot,
        forecast_snapshot=forecast_snapshot,
        resolver_rule=resolver_rule,
        probability_state=probability_state,
        comparison_row=comparison_row,
    )
    checks = audit["checks"]
    ready_for_bot = audit["ready_for_bot"]

    if ready_for_bot and bot_authorized:
        render_compact_note(
            "Market, resolver, forecast, probability and comparison are aligned. "
            "BOT authorization is ON; execution gateway still needs production risk gates.",
            tone="info",
        )
    elif ready_for_bot:
        render_compact_note(
            "The data chain is aligned for decision support, but BOT auto-execution is not authorized.",
            tone="info",
        )
    else:
        render_compact_note(
            "One or more pipeline layers are not aligned with the selected market. "
            "Use Activate & Run Pipeline before trusting the comparison.",
            tone="warning",
        )

    st.markdown(
        """
        <style>
        .alignment-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.42rem;
            margin-top: 0.45rem;
        }
        .alignment-card {
            min-height: 5.8rem;
            border: 1px solid rgba(35,72,82,0.14);
            border-radius: 14px;
            background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(248,246,239,0.86));
            box-shadow: 0 8px 22px rgba(49,77,75,0.055);
            padding: 0.58rem 0.66rem;
            position: relative;
            overflow: hidden;
        }
        .alignment-card::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 4px;
            background: rgba(102,119,130,0.32);
        }
        .alignment-card--ok::before { background: #0f9f71; }
        .alignment-card--warn::before { background: #c47a15; }
        .alignment-card--block::before { background: #c44d46; }
        .alignment-card-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
        }
        .alignment-name {
            color: #17252b;
            font-family: "Avenir Next Condensed", "DIN Condensed", "Trebuchet MS", sans-serif;
            font-size: 0.95rem;
            font-weight: 950;
            line-height: 1.05;
        }
        .alignment-pill {
            border-radius: 999px;
            padding: 0.12rem 0.44rem;
            font-family: "SF Mono", "Menlo", monospace;
            font-size: 0.56rem;
            font-weight: 900;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .alignment-pill--ok {
            background: rgba(15,159,113,0.12);
            color: #0f6f52;
        }
        .alignment-pill--warn {
            background: rgba(196,122,21,0.16);
            color: #8a540d;
        }
        .alignment-pill--block {
            background: rgba(196,77,70,0.13);
            color: #8d312c;
        }
        .alignment-detail {
            margin-top: 0.36rem;
            color: #17252b;
            font-size: 0.74rem;
            font-weight: 760;
            line-height: 1.22;
        }
        .alignment-ref {
            margin-top: 0.26rem;
            color: #667782;
            font-size: 0.65rem;
            line-height: 1.18;
        }
        @media (max-width: 900px) {
            .alignment-grid { grid-template-columns: minmax(0, 1fr); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    cards = []
    for check in checks:
        cards.append(_render_check_card(check))
    st.markdown(
        "<div class='alignment-grid'>" + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )

    with st.expander("Alignment Inputs", expanded=False):
        st.json(
            {
                "selected_market_id": audit["selected_market_id"],
                "selected_question": audit["selected_question"],
                "activated_market_id": audit["activated_market_id"],
                "forecast_market_id": audit["forecast_market_id"],
                "resolver_market_id": audit["resolver_market_id"],
                "probability_market_id": audit["probability_market_id"],
                "comparison_market_id": audit["comparison_market_id"],
                "validation_freshness_status": (
                    validation_freshness_status.get("status", "-")
                    if isinstance(validation_freshness_status, dict)
                    else "-"
                ),
                "label_coverage_status": (
                    label_coverage_report.get("status", "-")
                    if isinstance(label_coverage_report, dict)
                    else "-"
                ),
                "bot_authorized": bot_authorized,
                "ready_for_bot": ready_for_bot,
                "decision_note": "Shadow probability is heuristic and not calibrated.",
            }
        )


def _render_check_card(check: dict) -> str:
    level = check["level"]
    status = check["status"]
    return (
        f"<div class='alignment-card alignment-card--{escape(level)}'>"
        "<div class='alignment-card-top'>"
        f"<div class='alignment-name'>{escape(check['name'])}</div>"
        f"<span class='alignment-pill alignment-pill--{escape(level)}'>{escape(status)}</span>"
        "</div>"
        f"<div class='alignment-detail'>{escape(check['detail'])}</div>"
        f"<div class='alignment-ref'>{escape(check['ref'])}</div>"
        "</div>"
    )


def _selected_check(selected_market_snapshot: dict | None) -> dict:
    market_id = _market_id(selected_market_snapshot)
    if not market_id:
        return _check("Selected Market", "block", "missing", "No market selected.", "Choose a market in Watchlist.")
    return _check(
        "Selected Market",
        "ok",
        "selected",
        str(_value(selected_market_snapshot, "market_question") or market_id),
        f"market_id={market_id}",
    )


def _activated_input_check(selected_market_id: str, activated_market_snapshot: dict | None) -> dict:
    activated_id = _market_id(activated_market_snapshot)
    if not activated_id:
        return _check("Market Input", "block", "missing", "No activated realtime market input.", "Run Activate & Run Pipeline.")
    if selected_market_id and activated_id == selected_market_id:
        return _check(
            "Market Input",
            "ok",
            "aligned",
            "Activated realtime input matches the selected market.",
            f"market_id={activated_id} updated_at={_value(activated_market_snapshot, 'updated_at')}",
        )
    return _check(
        "Market Input",
        "warn",
        "mismatch",
        "Activated realtime input is for a different market.",
        f"selected={selected_market_id or '-'} input={activated_id}",
    )


def _forecast_check(selected_market_id: str, forecast_snapshot: dict | None) -> dict:
    forecast_id = _market_id(forecast_snapshot)
    if not forecast_id:
        return _check("Forecast", "block", "missing", "No forecast snapshot found.", "Run forecast once.")
    if selected_market_id and forecast_id == selected_market_id:
        return _check(
            "Forecast",
            "ok",
            "aligned",
            f"model_band={_value(forecast_snapshot, 'model_band')} value={_value(forecast_snapshot, 'value')}",
            f"source={_value(forecast_snapshot, 'source_mode')} timestamp={_value(forecast_snapshot, 'timestamp')}",
        )
    return _check(
        "Forecast",
        "warn",
        "mismatch",
        "Forecast snapshot is not for the selected market.",
        f"selected={selected_market_id or '-'} forecast={forecast_id}",
    )


def _resolver_check(selected_market_id: str, resolver_rule: dict | None) -> dict:
    resolver_id = _market_id(resolver_rule)
    status = str(_value(resolver_rule, "resolver_status") or "missing")
    source_match_grade = str(_value(resolver_rule, "source_match_grade") or "")
    source_policy = str(_value(resolver_rule, "official_vs_proxy_source") or "")
    if not resolver_id:
        return _check("Resolver", "block", "missing", "No resolver rule found for selected market.", "Run resolver once.")
    if resolver_id != selected_market_id:
        return _check("Resolver", "warn", "mismatch", "Resolver rule belongs to a different market.", f"resolver={resolver_id}")
    level = "ok" if status == "matched" else "warn"
    if source_match_grade in {"family_only", "unmatched"} or source_policy == "fallback":
        level = "warn"
    return _check(
        "Resolver",
        level,
        status,
        (
            f"family={_value(resolver_rule, 'market_family')} "
            f"source={_value(resolver_rule, 'required_data_source')} "
            f"match={source_match_grade or '-'}"
        ),
        (
            f"reason={_value(resolver_rule, 'resolver_reason')} "
            f"policy={source_policy or '-'}"
        ),
    )


def _probability_check(selected_market_id: str, probability_state: dict | None) -> dict:
    probability_id = _market_id(probability_state)
    if not probability_id:
        return _check("Probability", "warn", "missing", "No shadow probability state for selected market.", "Run probability shadow.")
    if probability_id != selected_market_id:
        return _check("Probability", "warn", "mismatch", "Probability state belongs to a different market.", f"probability={probability_id}")
    calibration = str(_value(probability_state, "calibration_status") or "-")
    return _check(
        "Probability",
        "ok",
        "shadow",
        f"fair_value={_value(probability_state, 'fair_value')} edge={_value(probability_state, 'edge')}",
        f"mode={_value(probability_state, 'mode')} calibration={calibration}",
    )


def _comparison_check(selected_market_id: str, comparison_row: dict | None) -> dict:
    comparison_id = _market_id(comparison_row)
    if not comparison_id:
        return _check("Comparison", "warn", "missing", "No latest dashboard comparison row for selected market.", "Run comparison once.")
    if comparison_id != selected_market_id:
        return _check("Comparison", "warn", "mismatch", "Comparison row belongs to a different market.", f"comparison={comparison_id}")
    status = str(_value(comparison_row, "comparison_status") or "-")
    level = "ok" if status in {"aligned", "mild_divergence", "strong_divergence"} else "warn"
    return _check(
        "Comparison",
        level,
        status,
        f"market_band={_value(comparison_row, 'market_band')} model_band={_value(comparison_row, 'model_band')}",
        f"gap={_value(comparison_row, 'confidence_adjusted_gap')} reason={_value(comparison_row, 'comparison_reason')}",
    )


def _check(name: str, level: str, status: str, detail: str, ref: str) -> dict:
    return {
        "name": name,
        "level": level,
        "status": status,
        "detail": detail,
        "ref": ref,
    }


def _market_id(payload: dict | None) -> str:
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("market_id") or "")


def _value(payload: dict | None, key: str) -> Any:
    if not isinstance(payload, dict):
        return None
    return payload.get(key)
