from __future__ import annotations

from typing import Any, cast

import streamlit as st

from weather_dashboard.lib.api import apiGet
from weather_dashboard.lib.api import apiPost
from weather_dashboard.types.weather import WeatherArchiveBundle
from weather_dashboard.types.weather import WeatherArchiveSummary
from weather_dashboard.types.weather import WeatherEvidenceArchiveRecord
from weather_dashboard.types.weather import WeatherForecastArchiveRecord
from weather_dashboard.types.weather import WeatherViewArchiveRecord
from weather_dashboard.ui.status_badge import render_status_badge

STATE_KEY = "pwb04f_weather_archive_state"
BUNDLE_MARKET_KEY = "pwb04f_weather_archive_market_id"


def build_weather_archive_panel_state() -> dict[str, object]:
    return {
        "summary": None,
        "forecasts": [],
        "evidence": [],
        "weather_views": [],
        "bundle": None,
        "message": None,
        "warnings": [],
    }


def _get_panel_state() -> dict[str, object]:
    state = st.session_state.get(STATE_KEY)
    if not isinstance(state, dict):
        state = build_weather_archive_panel_state()
        st.session_state[STATE_KEY] = state
    return state


def _set_message(state: dict[str, object], message: str | None) -> None:
    state["message"] = message


def load_summary(state: dict[str, object]) -> None:
    try:
        payload = cast(dict[str, Any], apiGet("/api/weather-archive/summary"))
        if payload.get("status") != "ok":
            _set_message(state, "Failed to load weather archive summary.")
            return
        state["summary"] = payload.get("summary")
        _set_message(state, "Weather archive summary loaded.")
    except Exception as exc:  # pragma: no cover
        _set_message(state, f"Failed to load weather archive summary: {exc}")


def load_recent_forecasts(state: dict[str, object]) -> None:
    try:
        payload = cast(dict[str, Any], apiGet("/api/weather-archive/forecasts?limit=50"))
        if payload.get("status") != "ok":
            _set_message(state, "Failed to load recent forecasts.")
            return
        items = list(payload.get("items") or [])
        state["forecasts"] = items
        _set_message(state, f"Loaded {len(items)} recent forecasts.")
    except Exception as exc:  # pragma: no cover
        _set_message(state, f"Failed to load recent forecasts: {exc}")


def load_recent_evidence(state: dict[str, object]) -> None:
    try:
        payload = cast(dict[str, Any], apiGet("/api/weather-archive/evidence?limit=50"))
        if payload.get("status") != "ok":
            _set_message(state, "Failed to load recent evidence.")
            return
        items = list(payload.get("items") or [])
        state["evidence"] = items
        _set_message(state, f"Loaded {len(items)} recent evidence records.")
    except Exception as exc:  # pragma: no cover
        _set_message(state, f"Failed to load recent evidence: {exc}")


def load_recent_weather_views(state: dict[str, object]) -> None:
    try:
        payload = cast(dict[str, Any], apiGet("/api/weather-archive/views?limit=50"))
        if payload.get("status") != "ok":
            _set_message(state, "Failed to load recent weather views.")
            return
        items = list(payload.get("items") or [])
        state["weather_views"] = items
        _set_message(state, f"Loaded {len(items)} recent weather views.")
    except Exception as exc:  # pragma: no cover
        _set_message(state, f"Failed to load recent weather views: {exc}")


def archive_latest_weather_view(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(BUNDLE_MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    try:
        payload = cast(dict[str, Any], apiPost(f"/api/weather-archive/latest/{market_id}", {}))
        if payload.get("status") != "ok":
            _set_message(state, "Archive latest weather view failed.")
            return
        state["warnings"] = list(payload.get("warnings") or [])
        load_summary(state)
        load_recent_forecasts(state)
        load_recent_evidence(state)
        load_recent_weather_views(state)
        _set_message(
            state,
            "Archived latest weather-side records from existing repository state.",
        )
    except Exception as exc:  # pragma: no cover
        _set_message(state, f"Archive latest weather view failed: {exc}")


def load_market_weather_bundle(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(BUNDLE_MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    try:
        payload = cast(dict[str, Any], apiGet(f"/api/weather-archive/market/{market_id}?limit=100"))
        if payload.get("status") != "ok":
            _set_message(state, "Failed to load market weather bundle.")
            return
        state["bundle"] = {
            "market_id": payload.get("market_id") or market_id,
            "forecasts": list(payload.get("forecasts") or []),
            "evidence": list(payload.get("evidence") or []),
            "weather_views": list(payload.get("weather_views") or []),
        }
        _set_message(state, f"Loaded weather archive bundle for {market_id}.")
    except Exception as exc:  # pragma: no cover
        _set_message(state, f"Failed to load market weather bundle: {exc}")


def _forecast_rows(items: list[WeatherForecastArchiveRecord]) -> list[dict[str, object]]:
    return [
        {
            "archived_at": item["archived_at"],
            "market_id": item["market_id"],
            "source_id": item["source_id"],
            "source_type": item["source_type"],
            "metric": item["metric"],
            "unit": item["unit"],
            "expected_value": item.get("expected_value"),
            "sigma": item.get("sigma"),
            "archive_reason": item["archive_reason"],
        }
        for item in items
    ]


def _evidence_rows(items: list[WeatherEvidenceArchiveRecord]) -> list[dict[str, object]]:
    return [
        {
            "archived_at": item["archived_at"],
            "market_id": item["market_id"],
            "evidence_pack_id": item["evidence_pack_id"],
            "source_ids": ", ".join(item.get("source_ids") or []),
            "evidence_summary": " | ".join(item.get("evidence_summary") or []),
            "archive_reason": item["archive_reason"],
        }
        for item in items
    ]


def _weather_view_rows(items: list[WeatherViewArchiveRecord]) -> list[dict[str, object]]:
    return [
        {
            "archived_at": item["archived_at"],
            "market_id": item["market_id"],
            "weather_view_id": item["weather_view_id"],
            "city": item.get("city"),
            "target_date": item.get("target_date"),
            "expected_value": item.get("expected_value"),
            "threshold": item.get("threshold"),
            "direction": item.get("direction"),
            "unit": item.get("unit"),
            "confidence": item.get("confidence"),
            "archive_reason": item["archive_reason"],
        }
        for item in items
    ]


def _bundle_summary(bundle: WeatherArchiveBundle | None) -> str:
    if not bundle:
        return "No market weather bundle loaded."
    return (
        f"Market `{bundle['market_id']}` with "
        f"{len(bundle.get('forecasts') or [])} forecasts, "
        f"{len(bundle.get('evidence') or [])} evidence records, and "
        f"{len(bundle.get('weather_views') or [])} weather views."
    )


def render_weather_forecast_archive_panel() -> None:
    state = _get_panel_state()
    st.markdown("### Weather Forecast Archive")
    st.caption(
        "Read-only archive of forecast inputs, evidence packs, and weather views for later calibration and backtest preparation. No trade, execute, auto calibrate, promote model, wallet, order, cancel, or go-live controls are exposed."
    )

    action_cols = st.columns(5, gap="small")
    actions = [
        ("Load Summary", load_summary),
        ("Load Recent Forecasts", load_recent_forecasts),
        ("Load Recent Evidence", load_recent_evidence),
        ("Load Recent Weather Views", load_recent_weather_views),
        ("Load Market Weather Bundle", load_market_weather_bundle),
    ]
    for col, (label, action) in zip(action_cols, actions):
        with col:
            if st.button(label, key=f"pwb04f_{label.lower().replace(' ', '_')}", use_container_width=True):
                action(state)

    lookup_cols = st.columns([2, 1], gap="small")
    with lookup_cols[0]:
        st.text_input(
            "Market ID",
            value=st.session_state.get(BUNDLE_MARKET_KEY, "tokyo_weather_market"),
            key=BUNDLE_MARKET_KEY,
        )
    with lookup_cols[1]:
        st.write("")
        st.write("")
        if st.button("Archive Latest Weather View", key="pwb04f_archive_latest", use_container_width=True):
            archive_latest_weather_view(state)

    if state.get("message"):
        st.info(str(state["message"]))

    summary = cast(WeatherArchiveSummary | None, state.get("summary"))
    if summary:
        st.markdown("#### Summary")
        metric_cols = st.columns(5)
        metric_cols[0].metric("Forecast Records", summary["forecast_records"])
        metric_cols[1].metric("Evidence Records", summary["evidence_records"])
        metric_cols[2].metric("Weather Views", summary["weather_view_records"])
        metric_cols[3].metric("Unique Markets", summary["unique_markets"])
        metric_cols[4].metric("Latest Archived", summary.get("latest_archived_at") or "—")
        badge_cols = st.columns(2)
        with badge_cols[0]:
            render_status_badge(f"By Source Type: {summary.get('by_source_type') or {}}")
        with badge_cols[1]:
            render_status_badge(f"By Reason: {summary.get('by_archive_reason') or {}}")
    else:
        st.caption("No weather archive summary loaded.")

    st.markdown("#### Recent Forecasts")
    forecast_rows = _forecast_rows(list(cast(list[WeatherForecastArchiveRecord], state.get("forecasts") or [])))
    if forecast_rows:
        st.dataframe(forecast_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No recent forecasts loaded.")

    st.markdown("#### Recent Evidence")
    evidence_rows = _evidence_rows(list(cast(list[WeatherEvidenceArchiveRecord], state.get("evidence") or [])))
    if evidence_rows:
        st.dataframe(evidence_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No recent evidence loaded.")

    st.markdown("#### Recent Weather Views")
    weather_view_rows = _weather_view_rows(list(cast(list[WeatherViewArchiveRecord], state.get("weather_views") or [])))
    if weather_view_rows:
        st.dataframe(weather_view_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No recent weather views loaded.")

    st.markdown("#### Market Weather Bundle")
    bundle = cast(WeatherArchiveBundle | None, state.get("bundle"))
    st.write(_bundle_summary(bundle))
    if bundle:
        st.caption("Forecasts")
        st.dataframe(_forecast_rows(list(bundle.get("forecasts") or [])), use_container_width=True, hide_index=True)
        st.caption("Evidence")
        st.dataframe(_evidence_rows(list(bundle.get("evidence") or [])), use_container_width=True, hide_index=True)
        st.caption("Weather Views")
        st.dataframe(_weather_view_rows(list(bundle.get("weather_views") or [])), use_container_width=True, hide_index=True)

    warnings = list(cast(list[str], state.get("warnings") or []))
    if warnings:
        st.markdown("#### Weather Archive Warnings")
        for warning in warnings:
            st.warning(warning, icon="!")
