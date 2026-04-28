from __future__ import annotations

from html import escape

import streamlit as st

from weather_dashboard.ui.compact_panel import semantic_tone, semantic_value_html


def _fmt(value: object, *, digits: int | None = None) -> str:
    if value is None or value == "":
        return "-"
    if digits is not None:
        try:
            return f"{float(value):.{digits}f}"
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def _shorten(value: object, limit: int = 120) -> str:
    text = _fmt(value)
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def build_operator_focus_summary(
    *,
    market_snapshot: dict | None,
    forecast_snapshot: dict | None,
    probability_state: dict | None,
    comparison_row: dict | None,
    compact_gate_summary: dict | None,
    unified_status_report: dict | None,
    position_snapshot: dict | None = None,
    production_readiness_report: dict | None = None,
) -> dict:
    market = _as_dict(market_snapshot)
    forecast = _as_dict(forecast_snapshot)
    probability = _as_dict(probability_state)
    comparison = _as_dict(comparison_row)
    gate = _as_dict(compact_gate_summary)
    unified = _as_dict(unified_status_report)
    operator = _as_dict(unified.get("operator"))
    execution = _as_dict(unified.get("execution"))
    production = _as_dict(production_readiness_report)
    position = _as_dict(position_snapshot)
    promotion_state = {}
    for candidate in (
        probability.get("promotion_state"),
        gate.get("promotion_state"),
        unified.get("promotion_state"),
    ):
        if isinstance(candidate, dict):
            promotion_state = candidate
            break

    block_reasons = [
        str(item)
        for item in (
            gate.get("blockers")
            or unified.get("block_reasons")
            or production.get("blockers")
            or []
        )
    ]

    return {
        "market_id": _fmt(market.get("market_id") or gate.get("selected_market_id")),
        "question": _shorten(market.get("market_question") or market.get("question"), 150),
        "family": _fmt(market.get("market_family")),
        "target_date": _fmt(market.get("target_date") or forecast.get("target_date")),
        "gate_status": _fmt(gate.get("gate_status") or execution.get("status")),
        "severity": _fmt(gate.get("severity") or "medium"),
        "recommended_action": _fmt(
            gate.get("recommended_operator_action") or "hold_execution_and_review"
        ),
        "probability_mode": _fmt(
            probability.get("probability_mode") or gate.get("probability_mode")
        ),
        "execution_constraint": _fmt(
            probability.get("execution_constraint") or gate.get("execution_constraint")
        ),
        "promotion_state": _fmt(
            promotion_state.get("probability_mode")
            or probability.get("probability_mode")
            or gate.get("promotion_state")
        ),
        "promotion_reason": _fmt(
            promotion_state.get("promotion_reason")
            or probability.get("promotion_reason")
            or gate.get("promotion_reason")
        ),
        "demotion_reason": _fmt(
            promotion_state.get("demotion_reason")
            or probability.get("demotion_reason")
            or gate.get("demotion_reason")
        ),
        "comparison_status": _fmt(comparison.get("comparison_status")),
        "confidence_adjusted_gap": _fmt(comparison.get("confidence_adjusted_gap"), digits=3),
        "edge": _fmt(probability.get("confidence_adjusted_edge"), digits=3),
        "market_probability": _fmt(market.get("market_probability"), digits=2),
        "resolver_gate": _fmt(gate.get("resolver_gate")),
        "freshness_gate": _fmt(gate.get("freshness_gate")),
        "authorization_gate": _fmt(gate.get("authorization_gate")),
        "execution_gate": _fmt(gate.get("execution_gate")),
        "gate_source": _fmt(gate.get("gate_source")),
        "operator_mode": _fmt(operator.get("operator_mode")),
        "can_bot_trade": _fmt(operator.get("can_bot_trade")),
        "production_ready": _fmt(
            production.get("production_ready")
            if "production_ready" in production
            else production.get("ready")
        ),
        "position_status": _fmt(
            position.get("status")
            or position.get("position_status")
            or position.get("exposure_status")
        ),
        "updated_at": _fmt(
            forecast.get("updated_at")
            or market.get("updated_at")
            or unified.get("generated_at")
            or unified.get("updated_at")
        ),
        "block_reasons": block_reasons,
    }


def _as_dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def render_operator_focus_banner(
    summary: dict,
    *,
    title: str,
    subtitle: str,
    fields: list[tuple[str, str]],
    blockers_limit: int = 4,
) -> None:
    _render_focus_styles()

    blockers = summary.get("block_reasons") or []
    blocker_text = ", ".join(str(item) for item in blockers[:blockers_limit]) if blockers else "none"
    if len(blockers) > blockers_limit:
        blocker_text += f" +{len(blockers) - blockers_limit}"
    status = str(summary.get("gate_status") or "-")
    severity = str(summary.get("severity") or "medium").lower()
    metrics_html = "\n".join(
        f"""
        <div class="operator-focus__metric">
          <span>{escape(label)}</span>
          <strong>{semantic_value_html(label, summary.get(key))}</strong>
        </div>
        """
        for label, key in fields
    )
    status_tone = semantic_tone("gate_status", status)

    st.markdown(
        f"""
        <section class="operator-focus operator-focus--{escape(severity)}">
          <div class="operator-focus__header">
            <div>
              <div class="operator-focus__eyebrow">Page Focus</div>
              <div class="operator-focus__title">{escape(title)}</div>
              <div class="operator-focus__subtitle">{escape(subtitle)}</div>
            </div>
            <div class="operator-focus__status operator-focus__status--{escape(status_tone)}">{escape(status)}</div>
          </div>
          <div class="operator-focus__market">
            <span>{escape(_fmt(summary.get("market_id")))}</span>
            <strong>{escape(_shorten(summary.get("question"), 180))}</strong>
          </div>
          <div class="operator-focus__metrics">
            {metrics_html}
          </div>
          <div class="operator-focus__action">
            <span>Promotion State</span>
            <strong>{semantic_value_html("Promotion State", summary.get("promotion_state"))}</strong>
          </div>
          <div class="operator-focus__action">
            <span>Promotion Reason</span>
            <strong>{semantic_value_html("Promotion Reason", summary.get("promotion_reason"))}</strong>
          </div>
          <div class="operator-focus__action">
            <span>Demotion Reason</span>
            <strong>{semantic_value_html("Demotion Reason", summary.get("demotion_reason"))}</strong>
          </div>
          <div class="operator-focus__action">
            <span>Next Action</span>
            <strong>{semantic_value_html("Next Action", summary.get("recommended_action"))}</strong>
          </div>
          <div class="operator-focus__blockers">
            <span>Blockers</span>
            <strong>{semantic_value_html("Blockers", blocker_text)}</strong>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_focus_styles() -> None:
    st.markdown(
        """
        <style>
        .operator-focus {
            margin: 0 0 0.42rem;
            padding: 0.48rem 0.58rem;
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 12px;
            background:
                radial-gradient(circle at 4% 0%, rgba(79, 143, 230, 0.10), transparent 30%),
                linear-gradient(135deg, rgba(16,20,26,0.98), rgba(12,15,20,0.98));
            box-shadow: none;
        }
        .operator-focus--high,
        .operator-focus--critical {
            border-color: rgba(217, 109, 103, 0.34);
            background:
                radial-gradient(circle at 6% 0%, rgba(217, 109, 103, 0.14), transparent 34%),
                linear-gradient(135deg, rgba(29,16,16,0.98), rgba(21,13,13,0.98));
        }
        .operator-focus__header {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 0.5rem;
            align-items: center;
        }
        .operator-focus__eyebrow,
        .operator-focus__metric span,
        .operator-focus__action span,
        .operator-focus__blockers span,
        .operator-focus__market span {
            color: #9aa3ad;
            font-family: "SF Mono", "Menlo", monospace;
            font-size: 0.62rem;
            font-weight: 900;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }
        .operator-focus__title {
            color: #f7fbff;
            font-family: "Avenir Next Condensed", "DIN Condensed", "Trebuchet MS", sans-serif;
            font-size: 1.12rem;
            font-weight: 950;
            line-height: 1.12;
        }
        .operator-focus__subtitle {
            color: #9aa3ad;
            font-size: 0.74rem;
            line-height: 1.3;
        }
        .operator-focus__status {
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 999px;
            background: rgba(255,255,255,0.05);
            color: #f7fbff;
            font-family: "SF Mono", "Menlo", monospace;
            font-size: 0.68rem;
            font-weight: 950;
            padding: 0.2rem 0.5rem;
            white-space: nowrap;
        }
        .operator-focus__status--ok {
            border-color: rgba(15, 159, 113, 0.28);
            background: rgba(15, 159, 113, 0.10);
            color: #8fe2b0;
        }
        .operator-focus__status--warning {
            border-color: rgba(215, 171, 87, 0.30);
            background: rgba(215, 171, 87, 0.10);
            color: #e6c67c;
        }
        .operator-focus__status--critical {
            border-color: rgba(217, 109, 103, 0.30);
            background: rgba(217, 109, 103, 0.10);
            color: #e5a09d;
        }
        .operator-focus__market {
            margin-top: 0.36rem;
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 12px;
            background: rgba(255,255,255,0.05);
            padding: 0.34rem 0.42rem;
        }
        .operator-focus__market strong {
            display: block;
            margin-top: 0.1rem;
            color: #f7fbff;
            font-size: 0.82rem;
            line-height: 1.22;
        }
        .operator-focus__metrics {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 0.28rem;
            margin-top: 0.32rem;
        }
        .operator-focus__metric,
        .operator-focus__action,
        .operator-focus__blockers {
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 10px;
            background: rgba(255,255,255,0.05);
            padding: 0.28rem 0.34rem;
        }
        .operator-focus__metric strong,
        .operator-focus__action strong,
        .operator-focus__blockers strong {
            display: block;
            margin-top: 0.1rem;
            font-size: 0.72rem;
            line-height: 1.18;
            overflow-wrap: anywhere;
        }
        .operator-focus__metric strong .semantic-value--ok,
        .operator-focus__action strong .semantic-value--ok,
        .operator-focus__blockers strong .semantic-value--ok {
            color: #8fe2b0;
        }
        .operator-focus__metric strong .semantic-value--warning,
        .operator-focus__action strong .semantic-value--warning,
        .operator-focus__blockers strong .semantic-value--warning {
            color: #e6c67c;
        }
        .operator-focus__metric strong .semantic-value--critical,
        .operator-focus__action strong .semantic-value--critical,
        .operator-focus__blockers strong .semantic-value--critical {
            color: #e5a09d;
        }
        .operator-focus__action,
        .operator-focus__blockers {
            margin-top: 0.3rem;
        }
        @media (max-width: 900px) {
            .operator-focus__metrics {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
