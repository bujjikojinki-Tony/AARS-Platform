from __future__ import annotations

from html import escape

import streamlit as st


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
    market = market_snapshot or {}
    forecast = forecast_snapshot or {}
    probability = probability_state or {}
    comparison = comparison_row or {}
    gate = compact_gate_summary or {}
    unified = unified_status_report or {}
    operator = unified.get("operator") or {}
    execution = unified.get("execution") or {}
    production = production_readiness_report or {}
    position = position_snapshot or {}

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
          <strong>{escape(_fmt(summary.get(key)))}</strong>
        </div>
        """
        for label, key in fields
    )

    st.markdown(
        f"""
        <section class="operator-focus operator-focus--{escape(severity)}">
          <div class="operator-focus__header">
            <div>
              <div class="operator-focus__eyebrow">Page Focus</div>
              <div class="operator-focus__title">{escape(title)}</div>
              <div class="operator-focus__subtitle">{escape(subtitle)}</div>
            </div>
            <div class="operator-focus__status">{escape(status)}</div>
          </div>
          <div class="operator-focus__market">
            <span>{escape(_fmt(summary.get("market_id")))}</span>
            <strong>{escape(_shorten(summary.get("question"), 180))}</strong>
          </div>
          <div class="operator-focus__metrics">
            {metrics_html}
          </div>
          <div class="operator-focus__action">
            <span>Next Action</span>
            <strong>{escape(_fmt(summary.get("recommended_action")))}</strong>
          </div>
          <div class="operator-focus__blockers">
            <span>Blockers</span>
            <strong>{escape(blocker_text)}</strong>
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
            border: 1px solid rgba(35, 72, 82, 0.16);
            border-radius: 14px;
            background:
                radial-gradient(circle at 4% 0%, rgba(196, 122, 21, 0.12), transparent 30%),
                linear-gradient(135deg, rgba(255,255,255,0.94), rgba(246,248,243,0.88));
            box-shadow: 0 12px 28px rgba(49, 77, 75, 0.07);
        }
        .operator-focus--high,
        .operator-focus--critical {
            border-color: rgba(196, 77, 70, 0.32);
            background:
                radial-gradient(circle at 6% 0%, rgba(196, 77, 70, 0.13), transparent 34%),
                linear-gradient(135deg, rgba(255,255,255,0.96), rgba(252,242,235,0.9));
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
            color: #667782;
            font-family: "SF Mono", "Menlo", monospace;
            font-size: 0.62rem;
            font-weight: 900;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }
        .operator-focus__title {
            color: #11282f;
            font-family: "Avenir Next Condensed", "DIN Condensed", "Trebuchet MS", sans-serif;
            font-size: 1.12rem;
            font-weight: 950;
            line-height: 1.12;
        }
        .operator-focus__subtitle {
            color: #667782;
            font-size: 0.74rem;
            line-height: 1.3;
        }
        .operator-focus__status {
            border: 1px solid rgba(35, 72, 82, 0.16);
            border-radius: 999px;
            background: rgba(255,255,255,0.76);
            color: #17252b;
            font-family: "SF Mono", "Menlo", monospace;
            font-size: 0.68rem;
            font-weight: 950;
            padding: 0.2rem 0.5rem;
            white-space: nowrap;
        }
        .operator-focus__market {
            margin-top: 0.36rem;
            border: 1px solid rgba(35, 72, 82, 0.12);
            border-radius: 12px;
            background: rgba(255,255,255,0.62);
            padding: 0.34rem 0.42rem;
        }
        .operator-focus__market strong {
            display: block;
            margin-top: 0.1rem;
            color: #17252b;
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
            border: 1px solid rgba(35, 72, 82, 0.12);
            border-radius: 10px;
            background: rgba(255,255,255,0.68);
            padding: 0.28rem 0.34rem;
        }
        .operator-focus__metric strong,
        .operator-focus__action strong,
        .operator-focus__blockers strong {
            display: block;
            margin-top: 0.1rem;
            color: #17252b;
            font-size: 0.72rem;
            line-height: 1.18;
            overflow-wrap: anywhere;
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
