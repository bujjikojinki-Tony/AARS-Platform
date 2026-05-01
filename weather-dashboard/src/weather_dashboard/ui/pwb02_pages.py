from __future__ import annotations

import json

import streamlit as st

from weather_dashboard.lib.api import apiGet
from weather_dashboard.lib.api import apiPost
from weather_dashboard.types.weather import WorkstationPayload
from weather_dashboard.ui.pwb02_components import (
    render_candidate_decision_card,
    render_evidence_pack_card,
    render_pipeline_node,
    render_probability_view_card,
    render_weather_descriptor_card,
    render_weather_sources_table,
    render_weather_view_card,
)
from weather_dashboard.ui.pwb03_components import (
    render_calibration_history_panel,
    render_probability_comparison_panel,
)


DEFAULT_MARKET_ID = "mock_weather_strong_yes"
DEFAULT_QUESTION = "Will Tokyo high temperature exceed 30C on June 1?"


def render_pwb02_evidence_raw_page() -> None:
    st.markdown("## Evidence / Raw")
    st.caption("Inspect parsed weather evidence, source records, and raw payloads.")
    market_id = st.text_input("Market ID", value=st.session_state.get("pwb02_evidence_market_id", DEFAULT_MARKET_ID))
    st.session_state["pwb02_evidence_market_id"] = market_id
    if st.button("Load Evidence", key="pwb02_evidence_load", use_container_width=True):
        st.session_state["pwb02_last_workstation_payload"] = apiGet(f"/api/workstation/{market_id}")
        st.rerun()

    payload = _current_payload(market_id)
    if payload is None:
        st.info("Load a market to inspect evidence.")
        return

    render_weather_descriptor_card(payload.get("descriptor"))
    render_evidence_pack_card(payload.get("evidence_pack"))
    render_weather_sources_table(payload.get("sources"))
    _render_raw_json(payload)


def render_pwb02_workstation_page() -> None:
    st.markdown("## Workstation")
    st.caption("Single-market weather evidence, probability, and decision console.")
    market_id = st.text_input("Market ID", value=st.session_state.get("pwb02_workstation_market_id", DEFAULT_MARKET_ID))
    st.session_state["pwb02_workstation_market_id"] = market_id

    button_cols = st.columns(4)
    if button_cols[0].button("Scan", key="pwb02_ws_scan", use_container_width=True):
        apiPost("/api/opportunities/scan")
        st.session_state["pwb02_last_workstation_payload"] = apiGet(f"/api/workstation/{market_id}")
        st.rerun()
    if button_cols[1].button("Load", key="pwb02_ws_load", use_container_width=True):
        st.session_state["pwb02_last_workstation_payload"] = apiGet(f"/api/workstation/{market_id}")
        st.rerun()
    if button_cols[2].button("Simulate", key="pwb02_ws_simulate", use_container_width=True):
        payload = _current_payload(market_id)
        candidate = (payload or {}).get("candidate") or {}
        candidate_id = candidate.get("candidate_id")
        if candidate_id:
            apiPost("/api/command", {"command": f"/simulate {candidate_id}"})
            st.session_state["pwb02_last_workstation_payload"] = apiGet(f"/api/workstation/{market_id}")
            st.rerun()
    if button_cols[3].button("Block", key="pwb02_ws_block", use_container_width=True):
        payload = _current_payload(market_id)
        candidate = (payload or {}).get("candidate") or {}
        candidate_id = candidate.get("candidate_id")
        if candidate_id:
            apiPost(f"/api/opportunities/{candidate_id}/block")
            st.session_state["pwb02_last_workstation_payload"] = apiGet(f"/api/workstation/{market_id}")
            st.rerun()

    if st.button("Compare", key="pwb03_ws_compare", use_container_width=True):
        apiPost(f"/api/probability/compare/{market_id}")
        st.session_state["pwb02_last_workstation_payload"] = apiGet(f"/api/workstation/{market_id}")
        st.rerun()

    payload = _current_payload(market_id)
    if payload is None:
        st.info("Load a market or run a scan to populate the workstation.")
        return

    render_candidate_decision_card(payload.get("candidate"))
    left, right = st.columns(2)
    with left:
        render_weather_descriptor_card(payload.get("descriptor"))
    with right:
        render_probability_view_card(payload.get("probability_view"))
    render_weather_view_card(payload.get("weather_view"))
    render_probability_comparison_panel(payload.get("probability_comparison"), on_compare=lambda: _compare_and_refresh(market_id))
    lower_left, lower_right = st.columns(2)
    with lower_left:
        render_evidence_pack_card(payload.get("evidence_pack"))
    with lower_right:
        render_weather_sources_table(payload.get("sources"))
    _render_raw_json(payload)


def render_pwb02_pipeline_page() -> None:
    st.markdown("## Pipeline")
    st.caption("Evidence-to-execution trace map for the weather probability chain.")
    nodes = [
        ("Market Discovery", "Load candidate markets from mock or future Polymarket source.", "READY"),
        ("Question Parsing", "Parse city, date, threshold, metric, unit, and direction.", "PWB-02"),
        ("Weather Source Fetch", "Fetch Open-Meteo mock/offline fallback and NOAA placeholder records.", "PWB-02"),
        ("Evidence Pack", "Build evidence freshness, conflict level, and raw refs.", "PWB-02"),
        ("Weather View", "Build expected value, range, sigma, confirmation and invalidation rules.", "PWB-02"),
        ("Probability View", "Compute Gaussian v0 model probability.", "PWB-02"),
        ("Risk Gate", "Reuse edge, liquidity, spread, and circuit-breaker checks.", "READY"),
        ("Simulation", "Run simulation-only decision flow. Live execution disabled.", "SAFE"),
    ]
    grid = st.columns(2)
    for index, (title, description, status) in enumerate(nodes):
        with grid[index % 2]:
            render_pipeline_node(title, description, status)


def _current_payload(market_id: str) -> WorkstationPayload | None:
    payload = st.session_state.get("pwb02_last_workstation_payload")
    if isinstance(payload, dict) and str(payload.get("market_id") or "") == str(market_id):
        return payload  # type: ignore[return-value]
    try:
        payload = apiGet(f"/api/workstation/{market_id}")
    except Exception as exc:
        st.error(str(exc))
        return None
    if isinstance(payload, dict):
        st.session_state["pwb02_last_workstation_payload"] = payload
        return payload  # type: ignore[return-value]
    return None


def _render_raw_json(payload: dict) -> None:
    with st.expander("Raw JSON", expanded=False):
        st.code(json.dumps(payload, indent=2, ensure_ascii=False), language="json")


def _compare_and_refresh(market_id: str) -> None:
    apiPost(f"/api/probability/compare/{market_id}")
    st.session_state["pwb02_last_workstation_payload"] = apiGet(f"/api/workstation/{market_id}")
    st.rerun()
