from __future__ import annotations

from html import escape

import streamlit as st

from weather_dashboard.ui.compact_panel import sanitize_text


def build_worker_health_strip_items(report: dict | None) -> list[dict]:
    if not report:
        return []
    items: list[dict] = []
    for worker in report.get("workers", []):
        if not isinstance(worker, dict):
            continue
        freshness_seconds = worker.get("freshness_seconds")
        freshness = "-"
        if isinstance(freshness_seconds, (int, float)):
            freshness = f"{int(freshness_seconds)}s"
        items.append(
            {
                "label": str(worker.get("label") or worker.get("worker") or "worker"),
                "status": str(worker.get("status") or "warning"),
                "freshness": freshness,
            }
        )
    return items


def render_worker_health_strip(report: dict | None) -> None:
    items = build_worker_health_strip_items(report)
    if not items:
        return

    chips = "".join(
        f"""
        <span class="worker-health-pill worker-health-pill--{escape(item['status'])}">
          <strong>{escape(sanitize_text(item['label']))}</strong>
          <em>{escape(sanitize_text(item['freshness']))}</em>
        </span>
        """
        for item in items
    )
    overall_status = escape(sanitize_text(report.get("overall_status") or "unknown"))
    st.markdown(
        f"""
        <section class="worker-health-strip">
          <div class="worker-health-strip__title">Worker Health</div>
          <div class="worker-health-strip__overall">Overall: {overall_status}</div>
          <div class="worker-health-strip__chips">{chips}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
