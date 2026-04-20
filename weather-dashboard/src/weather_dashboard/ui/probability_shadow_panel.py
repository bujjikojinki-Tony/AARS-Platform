from __future__ import annotations

import streamlit as st

from weather_dashboard.ui.compact_panel import render_compact_note, render_kv_section, render_panel_title


def render_probability_shadow_panel(probability_state: dict | None) -> None:
    render_panel_title("Probability Shadow")

    if not probability_state:
        st.info(
            "No probability shadow state found yet. "
            "Run weather-comparison-engine/scripts/run_probability_shadow.py."
        )
        return

    calibration_status = probability_state.get("calibration_status", "-")
    probability_mode = probability_state.get("probability_mode", "-")
    execution_constraint = probability_state.get("execution_constraint", "-")
    approved_for_live = probability_state.get("approved_for_live", "-")
    deployment_mode = probability_state.get("deployment_mode", "-")
    promotion_reason = probability_state.get("promotion_reason", "-")
    render_compact_note(
        "Shadow probability is a heuristic decision aid, not a calibrated probability. "
        "It does not affect current comparison history or BOT execution.",
        tone="warning" if calibration_status == "not_calibrated" else "info",
    )
    render_kv_section(
        "Fair Value Shadow",
        [
            ("Market ID", probability_state.get("market_id", "-")),
            ("Mode", probability_state.get("mode", "-")),
            ("Calibration", calibration_status),
            ("Probability Mode", probability_mode),
            ("Execution Constraint", execution_constraint),
            ("Approved For Live", approved_for_live),
            ("Deployment Mode", deployment_mode),
            ("Promotion Reason", promotion_reason),
            ("Method", probability_state.get("method", "-")),
            ("Market Implied Probability", probability_state.get("market_implied_probability", "-")),
            ("Model Probability", probability_state.get("model_probability", "-")),
            ("Fair Value", probability_state.get("fair_value", "-")),
            ("Edge", probability_state.get("edge", "-")),
            ("Confidence Adjusted Edge", probability_state.get("confidence_adjusted_edge", "-")),
            ("Confidence", probability_state.get("confidence", "-")),
            ("Resolver Status", probability_state.get("resolver_status", "-")),
            ("Market Family", probability_state.get("market_family", "-")),
            ("Required Source", probability_state.get("required_data_source", "-")),
            ("Band Scheme", probability_state.get("band_scheme", "-")),
            ("Market Band", probability_state.get("market_band", "-")),
            ("Model Band", probability_state.get("model_band", "-")),
            ("Expected Band", probability_state.get("expected_band", "-")),
            ("Reason", probability_state.get("probability_reason", "-")),
        ],
        metric_label="Fair Value",
        metric_value=probability_state.get("fair_value", "-"),
    )

    with st.expander("Raw Probability Shadow", expanded=False):
        st.json(probability_state)


def render_probability_shadow_report_panel(report: dict | None) -> None:
    render_panel_title("Probability Shadow Report")

    if not report:
        st.info(
            "No probability shadow report found yet. "
            "Run weather-comparison-engine/scripts/run_probability_shadow.py."
        )
        return

    render_compact_note(
        report.get(
            "decision_note",
            "Shadow probability is heuristic and not calibrated.",
        ),
        tone="warning",
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tracked", report.get("tracked_markets", "-"))
    c2.metric("Active", report.get("active_states", "-"))
    c3.metric("Blocked", report.get("blocked_states", "-"))
    c4.metric("Probability Mode", report.get("probability_mode", "-"))
    c5, c6, c7 = st.columns(3)
    c5.metric("Calibration", report.get("calibration_status", "-"))
    c6.metric("Approved For Live", report.get("approved_for_live", "-"))
    c7.metric("Deployment Mode", report.get("deployment_mode", "-"))

    top_edges = report.get("top_edges") or []
    if top_edges:
        st.markdown("**Top Shadow Edges**")
        st.dataframe(top_edges, use_container_width=True, hide_index=True)
    else:
        st.info("No active shadow edges yet.")

    cols = st.columns(2)
    with cols[0]:
        render_kv_section(
            "Blocked Reasons",
            sorted((report.get("blocked_reason_counts") or {}).items()),
        )
    with cols[1]:
        render_kv_section(
            "Market Families",
            sorted((report.get("market_family_counts") or {}).items()),
        )

    with st.expander("Raw Probability Shadow Report", expanded=False):
        st.json(report)
