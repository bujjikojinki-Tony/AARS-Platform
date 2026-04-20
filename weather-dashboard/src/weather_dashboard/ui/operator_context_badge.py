from __future__ import annotations

from html import escape

import streamlit as st


def build_operator_context_badge_context(context: dict | None) -> dict | None:
    if not context:
        return None
    market_id = str(context.get("market_id") or "").strip()
    if not market_id:
        return None
    return {
        "market_id": market_id,
        "label": str(context.get("label") or market_id),
        "selection_source": str(context.get("selection_source") or "-"),
        "market_family": str(context.get("market_family") or "-"),
        "comparison_status": str(context.get("comparison_status") or "-"),
        "action_hint": str(context.get("action_hint") or "-"),
        "probability_mode": str(context.get("probability_mode") or "-"),
        "generated_at": str(context.get("generated_at") or "-"),
    }


def render_operator_context_badge(context: dict | None) -> None:
    summary = build_operator_context_badge_context(context)
    if not summary:
        return

    st.markdown(
        f"""
        <section class="operator-context-badge">
          <div class="operator-context-badge__title">
            <span>Operator Market Context</span>
            <strong>Telegram default follows `{escape(summary['market_id'])}`</strong>
          </div>
          <div class="operator-context-badge__grid">
            <div><span>Label</span><strong>{escape(summary['label'])}</strong></div>
            <div><span>Source</span><strong>{escape(summary['selection_source'])}</strong></div>
            <div><span>Family</span><strong>{escape(summary['market_family'])}</strong></div>
            <div><span>Comparison</span><strong>{escape(summary['comparison_status'])}</strong></div>
            <div><span>Action</span><strong>{escape(summary['action_hint'])}</strong></div>
            <div><span>Probability</span><strong>{escape(summary['probability_mode'])}</strong></div>
          </div>
          <div class="operator-context-badge__footer">
            Last written: {escape(summary['generated_at'])}
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
