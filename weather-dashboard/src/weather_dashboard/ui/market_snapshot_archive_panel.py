from __future__ import annotations

from typing import Any, cast

import streamlit as st

from weather_dashboard.lib.api import apiGet
from weather_dashboard.lib.api import apiPost
from weather_dashboard.types.weather import MarketSnapshotArchiveRecord
from weather_dashboard.types.weather import MarketSnapshotSeries
from weather_dashboard.types.weather import SnapshotArchiveSummary
from weather_dashboard.ui.status_badge import render_status_badge

STATE_KEY = "pwb04e_snapshot_archive_state"
SERIES_MARKET_KEY = "pwb04e_snapshot_archive_market_id"


def build_snapshot_archive_panel_state() -> dict[str, object]:
    return {
        "summary": None,
        "recent_snapshots": [],
        "series": None,
        "message": None,
        "warnings": [],
    }


def _get_panel_state() -> dict[str, object]:
    state = st.session_state.get(STATE_KEY)
    if not isinstance(state, dict):
        state = build_snapshot_archive_panel_state()
        st.session_state[STATE_KEY] = state
    return state


def _set_message(state: dict[str, object], message: str | None) -> None:
    state["message"] = message


def load_summary(state: dict[str, object]) -> None:
    try:
        payload = cast(dict[str, Any], apiGet("/api/snapshots/archive/summary"))
        if payload.get("status") != "ok":
            _set_message(state, "Failed to load snapshot archive summary.")
            return
        state["summary"] = payload.get("summary")
        _set_message(state, "Snapshot archive summary loaded.")
    except Exception as exc:  # pragma: no cover - surfaced in UI
        _set_message(state, f"Failed to load snapshot archive summary: {exc}")


def load_recent_snapshots(state: dict[str, object]) -> None:
    try:
        payload = cast(dict[str, Any], apiGet("/api/snapshots/archive?limit=50"))
        if payload.get("status") != "ok":
            _set_message(state, "Failed to load recent snapshots.")
            return
        items = list(payload.get("items") or [])
        state["recent_snapshots"] = items
        _set_message(state, f"Loaded {len(items)} recent snapshots.")
    except Exception as exc:  # pragma: no cover - surfaced in UI
        _set_message(state, f"Failed to load recent snapshots: {exc}")


def archive_current_source(state: dict[str, object]) -> None:
    try:
        payload = cast(
            dict[str, Any],
            apiPost(
                "/api/snapshots/archive/current-source",
                {"limit": 50},
            ),
        )
        if payload.get("status") != "ok":
            _set_message(state, "Archive current source failed.")
            return
        state["warnings"] = list(payload.get("warnings") or [])
        _set_message(
            state,
            f"Archived {int(payload.get('archived_count') or 0)} snapshots from current source.",
        )
        load_summary(state)
        load_recent_snapshots(state)
    except Exception as exc:  # pragma: no cover - surfaced in UI
        _set_message(state, f"Archive current source failed: {exc}")


def load_market_series(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(SERIES_MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    try:
        payload = cast(dict[str, Any], apiGet(f"/api/snapshots/archive/market/{market_id}?limit=100"))
        if payload.get("status") != "ok":
            _set_message(state, "Failed to load market snapshot series.")
            return
        state["series"] = payload.get("series")
        _set_message(state, f"Loaded market series for {market_id}.")
    except Exception as exc:  # pragma: no cover - surfaced in UI
        _set_message(state, f"Failed to load market snapshot series: {exc}")


def _recent_rows(items: list[MarketSnapshotArchiveRecord]) -> list[dict[str, object]]:
    return [
        {
            "archived_at": item["archived_at"],
            "market_id": item["market_id"],
            "question": item["question"],
            "source": item["source"],
            "yes_price": item["yes_price"],
            "no_price": item["no_price"],
            "liquidity": item["liquidity"],
            "archive_reason": item["archive_reason"],
        }
        for item in items
    ]


def _series_rows(series: MarketSnapshotSeries | None) -> list[dict[str, object]]:
    if not series:
        return []
    return [
        {
            "archived_at": item["archived_at"],
            "yes_price": item["yes_price"],
            "no_price": item["no_price"],
            "liquidity": item["liquidity"],
            "spread": item["spread"],
            "source": item["source"],
            "archive_reason": item["archive_reason"],
        }
        for item in series["snapshots"]
    ]


def render_market_snapshot_archive_panel() -> None:
    state = _get_panel_state()
    st.markdown("### Market Snapshot Archive")
    st.caption(
        "Read-only archive of market snapshots for calibration, replay, and drift review. No trade, execute, wallet, order, cancel, auto trade, or go-live controls are exposed."
    )

    action_cols = st.columns(4, gap="small")
    actions = [
        ("Load Summary", load_summary),
        ("Load Recent Snapshots", load_recent_snapshots),
        ("Archive Current Source", archive_current_source),
        ("Load Market Series", load_market_series),
    ]
    for col, (label, action) in zip(action_cols, actions):
        with col:
            if label == "Load Market Series":
                continue
            if st.button(label, use_container_width=True):
                action(state)

    lookup_cols = st.columns([2, 1], gap="small")
    with lookup_cols[0]:
        st.text_input(
            "Market ID",
            value=st.session_state.get(SERIES_MARKET_KEY, "mock_weather_strong_yes"),
            key=SERIES_MARKET_KEY,
        )
    with lookup_cols[1]:
        st.write("")
        st.write("")
        if st.button("Load Market Series", key="pwb04e_load_market_series", use_container_width=True):
            load_market_series(state)

    if state.get("message"):
        st.info(str(state["message"]))

    summary = cast(SnapshotArchiveSummary | None, state.get("summary"))
    if summary:
        st.markdown("#### Summary")
        metric_cols = st.columns(4)
        metric_cols[0].metric("Total Snapshots", summary["total_snapshots"])
        metric_cols[1].metric("Unique Markets", summary["unique_markets"])
        metric_cols[2].metric("Latest Archived", summary.get("latest_archived_at") or "—")
        metric_cols[3].metric("Sources", len(summary.get("by_source") or {}))
        badge_cols = st.columns(2)
        with badge_cols[0]:
            render_status_badge(f"By Source: {summary.get('by_source') or {}}")
        with badge_cols[1]:
            render_status_badge(f"By Reason: {summary.get('by_archive_reason') or {}}")
    else:
        st.caption("No snapshot archive summary loaded.")

    st.markdown("#### Recent Snapshots")
    recent_rows = _recent_rows(
        list(cast(list[MarketSnapshotArchiveRecord], state.get("recent_snapshots") or []))
    )
    if recent_rows:
        st.dataframe(recent_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No recent snapshots loaded.")

    st.markdown("#### Market Series")
    series = cast(MarketSnapshotSeries | None, state.get("series"))
    if series:
        st.write(
            f"Market `{series['market_id']}` with {series['count']} snapshots from "
            f"`{series.get('first_archived_at') or '—'}` to `{series.get('last_archived_at') or '—'}`."
        )
        st.dataframe(_series_rows(series), use_container_width=True, hide_index=True)
    else:
        st.caption("No market series loaded.")

    warnings = list(cast(list[str], state.get("warnings") or []))
    if warnings:
        st.markdown("#### Archive Warnings")
        for warning in warnings:
            st.warning(warning, icon="!")
