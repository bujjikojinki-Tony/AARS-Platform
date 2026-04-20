from __future__ import annotations

from html import escape

import streamlit as st

from weather_dashboard.ui.compact_panel import sanitize_text


def build_pipeline_sync_context(
    *,
    selected_market_id: str | None,
    operator_context: dict | None,
    last_sync_result: dict | None,
) -> dict:
    selected = str(selected_market_id or "").strip()
    operator_market_id = str((operator_context or {}).get("market_id") or "").strip()
    last_sync_market_id = str((last_sync_result or {}).get("market_id") or "").strip()
    last_sync_ok = bool((last_sync_result or {}).get("ok", False))
    return {
        "selected_market_id": selected or "-",
        "operator_market_id": operator_market_id or "-",
        "last_sync_market_id": last_sync_market_id or "-",
        "last_sync_ok": last_sync_ok,
        "operator_matches_selected": bool(selected and operator_market_id and selected == operator_market_id),
        "last_sync_matches_selected": bool(selected and last_sync_market_id and selected == last_sync_market_id),
        "last_sync_ran_at": str((last_sync_result or {}).get("ran_at") or "-"),
    }


def render_pipeline_sync_context(context: dict) -> None:
    operator_status = "aligned" if context["operator_matches_selected"] else "not aligned"
    sync_status = (
        "synced"
        if context["last_sync_matches_selected"] and context["last_sync_ok"]
        else ("failed" if context["last_sync_matches_selected"] else "not synced")
    )
    st.markdown(
        f"""
        <section class="pipeline-sync-context">
          <div><span>Selected</span><strong>{escape(sanitize_text(context['selected_market_id']))}</strong></div>
          <div><span>Telegram Default</span><strong>{escape(sanitize_text(context['operator_market_id']))} · {escape(sanitize_text(operator_status))}</strong></div>
          <div><span>Last Pipeline Sync</span><strong>{escape(sanitize_text(context['last_sync_market_id']))} · {escape(sanitize_text(sync_status))}</strong></div>
          <div><span>Last Sync At</span><strong>{escape(sanitize_text(context['last_sync_ran_at']))}</strong></div>
        </section>
        """,
        unsafe_allow_html=True,
    )
