from __future__ import annotations

import streamlit as st

from weather_dashboard.ui.compact_panel import render_kv_section, render_panel_title


def build_manual_advisory_reconciliation_summary(report: dict | None) -> dict:
    if not report:
        return {
            "available": False,
            "overall_status": "missing",
            "fill_count": 0,
            "reconciled_count": 0,
            "needs_review_count": 0,
            "unmatched_count": 0,
            "latest_market_id": "-",
            "latest_review_reason": "-",
        }

    items = [item for item in report.get("items", []) if isinstance(item, dict)]
    latest = items[-1] if items else {}
    return {
        "available": True,
        "overall_status": report.get("overall_status", "-"),
        "fill_count": report.get("fill_count", 0),
        "reconciled_count": report.get("reconciled_count", 0),
        "needs_review_count": report.get("needs_review_count", 0),
        "unmatched_count": report.get("unmatched_count", 0),
        "latest_market_id": latest.get("market_id", "-"),
        "latest_review_reason": latest.get("review_reason") or "-",
    }


def render_manual_advisory_reconciliation_panel(report: dict | None) -> None:
    render_panel_title(
        "Manual Advisory Reconciliation",
        "人工成交回填 vs position snapshot；仅用于人工下单后的核对，不代表 BOT 自动执行。",
    )
    summary = build_manual_advisory_reconciliation_summary(report)
    if not summary["available"]:
        st.info("No human fill reconciliation report found.")
        return

    render_kv_section(
        "Human Fill Check",
        [
            ("Overall Status", summary["overall_status"]),
            ("Fill Count", summary["fill_count"]),
            ("Reconciled", summary["reconciled_count"]),
            ("Needs Review", summary["needs_review_count"]),
            ("Unmatched", summary["unmatched_count"]),
            ("Latest Market", summary["latest_market_id"]),
            ("Latest Review Reason", summary["latest_review_reason"]),
        ],
        metric_label="Manual",
        metric_value=summary["overall_status"],
    )
