from __future__ import annotations

from typing import Any, cast

import streamlit as st

from weather_dashboard.lib.api import apiGet
from weather_dashboard.lib.api import apiPost
from weather_dashboard.types.weather import MarketOutcomeRecordV2
from weather_dashboard.types.weather import OutcomeArchiveSummary
from weather_dashboard.types.weather import OutcomeBundle
from weather_dashboard.types.weather import OutcomeResolutionRecordV2
from weather_dashboard.types.weather import WeatherActualRecordV2

STATE_KEY = "pwb04g_outcome_state"
MARKET_KEY = "pwb04g_market_id"
MARKET_FORM_KEY = "pwb04g_manual_market_id"
ACTUAL_FORM_KEY = "pwb04g_manual_actual_market_id"


def build_outcome_panel_state() -> dict[str, object]:
    return {
        "summary": None,
        "markets": [],
        "weather_actuals": [],
        "resolutions": [],
        "bundle": None,
        "message": None,
    }


def _get_panel_state() -> dict[str, object]:
    state = st.session_state.get(STATE_KEY)
    if not isinstance(state, dict):
        state = build_outcome_panel_state()
        st.session_state[STATE_KEY] = state
    return state


def _message(state: dict[str, object], text: str) -> None:
    state["message"] = text


def load_summary(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/outcomes/summary"))
    if payload.get("status") != "ok":
        _message(state, "Failed to load outcome summary.")
        return
    state["summary"] = payload.get("summary")
    _message(state, "Outcome summary loaded.")


def load_markets(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/outcomes/markets?limit=50"))
    if payload.get("status") != "ok":
        _message(state, "Failed to load market outcomes.")
        return
    items = list(payload.get("items") or [])
    state["markets"] = items
    _message(state, f"Loaded {len(items)} market outcomes.")


def load_weather_actuals(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/outcomes/weather-actuals?limit=50"))
    if payload.get("status") != "ok":
        _message(state, "Failed to load weather actuals.")
        return
    items = list(payload.get("items") or [])
    state["weather_actuals"] = items
    _message(state, f"Loaded {len(items)} weather actuals.")


def load_resolutions(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/outcomes/resolutions?limit=50"))
    if payload.get("status") != "ok":
        _message(state, "Failed to load resolutions.")
        return
    items = list(payload.get("items") or [])
    state["resolutions"] = items
    _message(state, f"Loaded {len(items)} resolutions.")


def load_bundle(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _message(state, "Market ID is required.")
        return
    payload = cast(dict[str, Any], apiGet(f"/api/outcomes/market/{market_id}?limit=100"))
    if payload.get("status") != "ok":
        _message(state, "Failed to load market outcome bundle.")
        return
    state["bundle"] = payload.get("bundle")
    _message(state, f"Loaded outcome bundle for {market_id}.")


def submit_manual_market_outcome(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_FORM_KEY, "")).strip()
    if not market_id:
        _message(state, "Manual market outcome requires market ID.")
        return
    payload = cast(
        dict[str, Any],
        apiPost(
            "/api/outcomes/market",
            {
                "market_id": market_id,
                "question": st.session_state.get("pwb04g_market_question") or None,
                "resolved_outcome": st.session_state.get("pwb04g_market_outcome") or "UNKNOWN",
                "resolution_status": st.session_state.get("pwb04g_market_status") or "UNKNOWN",
                "resolved_value": st.session_state.get("pwb04g_market_value"),
                "notes": st.session_state.get("pwb04g_market_notes") or None,
            },
        ),
    )
    if payload.get("status") != "ok":
        _message(state, str(payload.get("message") or "Failed to save market outcome."))
        return
    load_summary(state)
    load_markets(state)
    _message(state, "Manual market outcome saved.")


def submit_manual_weather_actual(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(ACTUAL_FORM_KEY, "")).strip()
    if not market_id:
        _message(state, "Manual weather actual requires market ID.")
        return
    payload = cast(
        dict[str, Any],
        apiPost(
            "/api/outcomes/weather-actual",
            {
                "market_id": market_id,
                "city": st.session_state.get("pwb04g_actual_city") or None,
                "target_date": st.session_state.get("pwb04g_actual_date") or None,
                "source": st.session_state.get("pwb04g_actual_source") or "MANUAL",
                "metric": st.session_state.get("pwb04g_actual_metric") or "temperature_high",
                "unit": st.session_state.get("pwb04g_actual_unit") or "C",
                "actual_value": st.session_state.get("pwb04g_actual_value"),
            },
        ),
    )
    if payload.get("status") != "ok":
        _message(state, str(payload.get("message") or "Failed to save weather actual."))
        return
    load_summary(state)
    load_weather_actuals(state)
    _message(state, "Manual weather actual saved.")


def submit_resolution(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    weather_actual_id = str(st.session_state.get("pwb04g_resolve_actual_id", "")).strip()
    if not market_id or not weather_actual_id:
        _message(state, "Resolve-from-weather requires market ID and weather actual ID.")
        return
    payload = cast(
        dict[str, Any],
        apiPost(
            "/api/outcomes/resolve-from-weather",
            {
                "market_id": market_id,
                "weather_actual_id": weather_actual_id,
                "threshold": st.session_state.get("pwb04g_resolve_threshold"),
                "direction": st.session_state.get("pwb04g_resolve_direction") or "UNKNOWN",
                "notes": st.session_state.get("pwb04g_resolve_notes") or None,
            },
        ),
    )
    if payload.get("status") != "ok":
        _message(state, str(payload.get("message") or "Failed to resolve outcome."))
        return
    load_summary(state)
    load_resolutions(state)
    _message(state, "Outcome resolution saved from weather actual.")


def _market_rows(items: list[MarketOutcomeRecordV2]) -> list[dict[str, object]]:
    return [
        {
            "resolved_at": item["resolved_at"],
            "market_id": item["market_id"],
            "source": item["source"],
            "resolved_outcome": item["resolved_outcome"],
            "resolution_status": item["resolution_status"],
            "resolved_value": item.get("resolved_value"),
        }
        for item in items
    ]


def _actual_rows(items: list[WeatherActualRecordV2]) -> list[dict[str, object]]:
    return [
        {
            "observed_at": item["observed_at"],
            "weather_actual_id": item["weather_actual_id"],
            "market_id": item["market_id"],
            "source": item["source"],
            "metric": item["metric"],
            "unit": item["unit"],
            "actual_value": item.get("actual_value"),
        }
        for item in items
    ]


def _resolution_rows(items: list[OutcomeResolutionRecordV2]) -> list[dict[str, object]]:
    return [
        {
            "resolved_at": item["resolved_at"],
            "market_id": item["market_id"],
            "weather_actual_id": item.get("weather_actual_id"),
            "direction": item["direction"],
            "actual_value": item.get("actual_value"),
            "threshold": item.get("threshold"),
            "resolved_outcome": item["resolved_outcome"],
            "resolution_status": item["resolution_status"],
        }
        for item in items
    ]


def render_outcome_resolver_panel() -> None:
    state = _get_panel_state()
    st.markdown("### Outcome Resolver")
    st.caption(
        "Read-only and manual outcome-resolution surface. No trade, execute, auto calibrate, promote model, backtest, wallet, order, cancel, or go-live controls are exposed."
    )

    top_actions = st.columns(5, gap="small")
    actions = [
        ("Load Summary", load_summary),
        ("Load Recent Market Outcomes", load_markets),
        ("Load Recent Weather Actuals", load_weather_actuals),
        ("Load Recent Resolutions", load_resolutions),
        ("Load Market Outcome Bundle", load_bundle),
    ]
    for col, (label, fn) in zip(top_actions, actions):
        with col:
            if st.button(label, key=f"pwb04g_{label.lower().replace(' ', '_')}", use_container_width=True):
                fn(state)

    st.text_input("Bundle Market ID", value=st.session_state.get(MARKET_KEY, "tokyo_weather_market"), key=MARKET_KEY)

    if state.get("message"):
        st.info(str(state["message"]))

    summary = cast(OutcomeArchiveSummary | None, state.get("summary"))
    if summary:
        cols = st.columns(5)
        cols[0].metric("Market Outcomes", summary["market_outcome_records"])
        cols[1].metric("Weather Actuals", summary["weather_actual_records"])
        cols[2].metric("Resolutions", summary["outcome_resolution_records"])
        cols[3].metric("Unique Markets", summary["unique_markets"])
        cols[4].metric("Latest", summary.get("latest_resolved_at") or "—")
        st.caption(f"By Resolution Status: {summary.get('by_resolution_status') or {}}")
        st.caption(f"By Resolved Outcome: {summary.get('by_resolved_outcome') or {}}")

    st.markdown("#### Manual Market Outcome")
    form_cols = st.columns(3, gap="small")
    form_cols[0].text_input("Market ID", value="tokyo_weather_market", key=MARKET_FORM_KEY)
    form_cols[1].text_input("Question", value="Will Tokyo high temperature exceed 30C on June 1?", key="pwb04g_market_question")
    form_cols[2].selectbox("Resolved Outcome", ["UNKNOWN", "YES", "NO", "INSUFFICIENT_EVIDENCE"], key="pwb04g_market_outcome")
    form_cols2 = st.columns(3, gap="small")
    form_cols2[0].selectbox("Resolution Status", ["UNKNOWN", "PENDING", "RESOLVED", "INSUFFICIENT_EVIDENCE"], key="pwb04g_market_status")
    form_cols2[1].number_input("Resolved Value", value=31.2, key="pwb04g_market_value")
    form_cols2[2].text_input("Notes", value="Manual operator outcome record.", key="pwb04g_market_notes")
    if st.button("Save Manual Market Outcome", key="pwb04g_save_market_outcome", use_container_width=True):
        submit_manual_market_outcome(state)

    st.markdown("#### Manual Weather Actual")
    actual_cols = st.columns(4, gap="small")
    actual_cols[0].text_input("Market ID ", value="tokyo_weather_market", key=ACTUAL_FORM_KEY)
    actual_cols[1].text_input("City", value="Tokyo", key="pwb04g_actual_city")
    actual_cols[2].text_input("Target Date", value="2026-06-01", key="pwb04g_actual_date")
    actual_cols[3].selectbox("Source", ["MANUAL", "OBSERVATION", "OPEN_METEO", "NOAA_PLACEHOLDER", "UNKNOWN"], key="pwb04g_actual_source")
    actual_cols2 = st.columns(3, gap="small")
    actual_cols2[0].selectbox("Metric", ["temperature_high", "temperature_low", "rainfall", "snowfall", "wind", "unknown"], key="pwb04g_actual_metric")
    actual_cols2[1].selectbox("Unit", ["C", "F", "MM", "INCH", "MPS", "UNKNOWN"], key="pwb04g_actual_unit")
    actual_cols2[2].number_input("Actual Value", value=31.2, key="pwb04g_actual_value")
    if st.button("Save Manual Weather Actual", key="pwb04g_save_weather_actual", use_container_width=True):
        submit_manual_weather_actual(state)

    st.markdown("#### Resolve From Weather Actual")
    resolve_cols = st.columns(4, gap="small")
    resolve_cols[0].text_input("Weather Actual ID", value="", key="pwb04g_resolve_actual_id")
    resolve_cols[1].number_input("Threshold Override", value=30.0, key="pwb04g_resolve_threshold")
    resolve_cols[2].selectbox("Direction", ["UNKNOWN", "ABOVE", "BELOW"], key="pwb04g_resolve_direction")
    resolve_cols[3].text_input("Resolution Notes", value="Manual read-only resolution from weather actual.", key="pwb04g_resolve_notes")
    if st.button("Resolve From Weather Actual", key="pwb04g_resolve_from_weather", use_container_width=True):
        submit_resolution(state)

    st.markdown("#### Recent Market Outcomes")
    market_rows = _market_rows(list(cast(list[MarketOutcomeRecordV2], state.get("markets") or [])))
    if market_rows:
        st.dataframe(market_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No market outcomes loaded.")

    st.markdown("#### Recent Weather Actuals")
    actual_rows = _actual_rows(list(cast(list[WeatherActualRecordV2], state.get("weather_actuals") or [])))
    if actual_rows:
        st.dataframe(actual_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No weather actuals loaded.")

    st.markdown("#### Recent Resolutions")
    resolution_rows = _resolution_rows(list(cast(list[OutcomeResolutionRecordV2], state.get("resolutions") or [])))
    if resolution_rows:
        st.dataframe(resolution_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No resolutions loaded.")

    st.markdown("#### Market Outcome Bundle")
    bundle = cast(OutcomeBundle | None, state.get("bundle"))
    if bundle:
        st.caption(
            f"Market `{bundle['market_id']}` with {len(bundle.get('markets') or [])} market outcomes, "
            f"{len(bundle.get('weather_actuals') or [])} weather actuals, and {len(bundle.get('resolutions') or [])} resolutions."
        )
        st.dataframe(_market_rows(list(bundle.get("markets") or [])), use_container_width=True, hide_index=True)
        st.dataframe(_actual_rows(list(bundle.get("weather_actuals") or [])), use_container_width=True, hide_index=True)
        st.dataframe(_resolution_rows(list(bundle.get("resolutions") or [])), use_container_width=True, hide_index=True)
    else:
        st.caption("No market outcome bundle loaded.")
