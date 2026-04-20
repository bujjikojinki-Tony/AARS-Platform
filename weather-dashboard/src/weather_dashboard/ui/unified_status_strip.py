from __future__ import annotations

from html import escape

import streamlit as st

from weather_dashboard.ui.compact_panel import sanitize_text


def build_unified_status_strip_summary(report: dict | None) -> dict | None:
    if not report:
        return None
    current_market = report.get("current_market") or {}
    probability = report.get("probability") or {}
    validation = report.get("validation") or {}
    execution = report.get("execution") or {}
    operator = report.get("operator") or {}
    return {
        "overall_status": str(report.get("overall_status") or "unknown"),
        "market_id": str(current_market.get("market_id") or "-"),
        "comparison_status": str(current_market.get("comparison_status") or "-"),
        "probability_mode": str(probability.get("probability_mode") or "-"),
        "execution_constraint": str(probability.get("execution_constraint") or "-"),
        "validation_freshness": str(validation.get("freshness_status") or "-"),
        "label_coverage": str(validation.get("label_coverage_status") or "-"),
        "execution_status": str(execution.get("status") or "-"),
        "can_bot_trade": bool(operator.get("can_bot_trade", False)),
        "operator_mode": str(operator.get("operator_mode") or "-"),
        "mode_badge_label": str((operator.get("mode_badge") or {}).get("label") or "-"),
        "block_reasons": [str(item) for item in report.get("block_reasons") or []],
    }


def render_unified_status_strip(report: dict | None) -> None:
    summary = build_unified_status_strip_summary(report)
    if not summary:
        return

    blockers = ", ".join(summary["block_reasons"][:4]) if summary["block_reasons"] else "none"
    st.markdown(
        f"""
        <section class="unified-status-strip">
          <div class="unified-status-strip__title">
            <span class="eyebrow">Unified Status Model</span>
            <strong>Overall {escape(sanitize_text(summary['overall_status']))}</strong>
          </div>
          <div class="unified-status-strip__metrics">
            <div><span>Market</span><strong>{escape(sanitize_text(summary['market_id']))}</strong></div>
            <div><span>Comparison</span><strong>{escape(sanitize_text(summary['comparison_status']))}</strong></div>
            <div><span>Probability</span><strong>{escape(sanitize_text(summary['probability_mode']))}</strong></div>
            <div><span>Constraint</span><strong>{escape(sanitize_text(summary['execution_constraint']))}</strong></div>
            <div><span>Validation</span><strong>{escape(sanitize_text(summary['validation_freshness']))}</strong></div>
            <div><span>Coverage</span><strong>{escape(sanitize_text(summary['label_coverage']))}</strong></div>
            <div><span>Gateway</span><strong>{escape(sanitize_text(summary['execution_status']))}</strong></div>
            <div><span>Mode</span><strong>{escape(sanitize_text(summary['mode_badge_label']))}</strong></div>
            <div><span>BOT Can Move</span><strong>{escape(str(summary['can_bot_trade']))}</strong></div>
          </div>
          <div class="unified-status-strip__blockers">
            <span>Block Reasons</span>
            <strong>{escape(sanitize_text(blockers))}</strong>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
