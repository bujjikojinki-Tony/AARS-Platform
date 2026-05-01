from __future__ import annotations

from typing import Any, cast

import streamlit as st

from weather_dashboard.lib.api import apiGet
from weather_dashboard.lib.api import apiPost
from weather_dashboard.types.weather import EmosShadowDiagnosticRecord
from weather_dashboard.types.weather import EmosShadowMarketBundle
from weather_dashboard.types.weather import EmosShadowRunRecord
from weather_dashboard.types.weather import EmosShadowSummary

STATE_KEY = "pwb05b_emos_shadow_state"
MARKET_KEY = "pwb05b_emos_market_id"


def build_emos_shadow_panel_state() -> dict[str, object]:
    return {
        "summary": None,
        "runs": [],
        "diagnostics": [],
        "bundle": None,
        "message": None,
        "raw_state": {},
    }


def _state() -> dict[str, object]:
    state = st.session_state.get(STATE_KEY)
    if not isinstance(state, dict):
        state = build_emos_shadow_panel_state()
        st.session_state[STATE_KEY] = state
    return state


def _set_message(state: dict[str, object], message: str) -> None:
    state["message"] = message


def load_summary(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/emos-shadow/summary"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load EMOS shadow summary.")
        return
    state["summary"] = payload.get("summary")
    state["raw_state"] = payload
    _set_message(state, "EMOS shadow summary loaded.")


def load_runs(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/emos-shadow/runs?limit=50"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load EMOS shadow runs.")
        return
    state["runs"] = list(payload.get("items") or [])
    state["raw_state"] = payload
    _set_message(state, f"Loaded {len(state['runs'])} EMOS shadow runs.")


def load_diagnostics(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/emos-shadow/diagnostics?limit=50"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load EMOS shadow diagnostics.")
        return
    state["diagnostics"] = list(payload.get("items") or [])
    state["raw_state"] = payload
    _set_message(state, f"Loaded {len(state['diagnostics'])} EMOS shadow diagnostics.")


def load_bundle(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    payload = cast(dict[str, Any], apiGet(f"/api/emos-shadow/market/{market_id}?limit=100"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load EMOS shadow market bundle.")
        return
    state["bundle"] = payload.get("bundle")
    state["raw_state"] = payload
    _set_message(state, f"Loaded EMOS shadow bundle for {market_id}.")


def build_shadow(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    payload = cast(dict[str, Any], apiPost("/api/emos-shadow/build", {"market_id": market_id}))
    state["raw_state"] = payload
    if payload.get("status") != "ok":
        _set_message(state, str(payload.get("message") or "EMOS shadow build failed."))
        return
    _set_message(state, f"Built EMOS shadow run for {market_id}.")
    load_summary(state)
    load_runs(state)
    load_diagnostics(state)


def build_all_shadow(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiPost("/api/emos-shadow/build-all", {}))
    state["raw_state"] = payload
    if payload.get("status") != "ok":
        _set_message(state, str(payload.get("message") or "Build-all EMOS shadow failed."))
        return
    _set_message(state, f"Built {payload.get('built_count', 0)} EMOS shadow runs.")
    load_summary(state)
    load_runs(state)
    load_diagnostics(state)


def _run_rows(items: list[EmosShadowRunRecord]) -> list[dict[str, object]]:
    return [
        {
            "created_at": item["created_at"],
            "market_id": item["market_id"],
            "engine_id": item.get("engine_id"),
            "base_probability": item.get("base_probability"),
            "emos_probability": item.get("emos_probability"),
            "location_adjustment": item.get("location_adjustment"),
            "scale_adjustment": item.get("scale_adjustment"),
            "sample_count": item.get("sample_count"),
            "run_status": item["run_status"],
        }
        for item in items
    ]


def _diagnostic_rows(items: list[EmosShadowDiagnosticRecord]) -> list[dict[str, object]]:
    return [
        {
            "created_at": item["created_at"],
            "market_id": item["market_id"],
            "sample_count": item.get("sample_count"),
            "avg_model_brier_score": item.get("avg_model_brier_score"),
            "avg_market_brier_score": item.get("avg_market_brier_score"),
            "avg_probability_error": item.get("avg_probability_error"),
            "avg_absolute_error": item.get("avg_absolute_error"),
            "location_weight": item.get("location_weight"),
            "scale_weight": item.get("scale_weight"),
        }
        for item in items
    ]


def _bundle_summary(bundle: EmosShadowMarketBundle | None) -> str:
    if not bundle:
        return "No EMOS shadow market bundle loaded."
    return (
        f"Market `{bundle['market_id']}` with "
        f"{len(bundle.get('runs') or [])} shadow runs and "
        f"{len(bundle.get('diagnostics') or [])} diagnostics."
    )


def render_emos_shadow_panel() -> None:
    state = _state()
    st.markdown("### EMOS Shadow")
    st.caption(
        "Read-only EMOS shadow computation from accepted calibration memory only. No trade, execute, simulate, promote model, auto calibrate, wallet, order, cancel, or go-live controls are exposed."
    )

    st.text_input("Market ID", value=st.session_state.get(MARKET_KEY, "tokyo_weather_market"), key=MARKET_KEY)

    action_cols = st.columns(3, gap="small")
    actions = [
        ("Load Summary", load_summary),
        ("Load Recent Runs", load_runs),
        ("Load Diagnostics", load_diagnostics),
        ("Build Shadow Run", build_shadow),
        ("Build All Eligible", build_all_shadow),
        ("Load Market Bundle", load_bundle),
    ]
    for idx, (label, fn) in enumerate(actions):
        col = action_cols[idx % 3]
        with col:
            if st.button(label, key=f"pwb05b_{label.lower().replace(' ', '_')}", use_container_width=True):
                fn(state)

    if state.get("message"):
        st.info(str(state["message"]))

    summary = cast(EmosShadowSummary | None, state.get("summary"))
    if summary:
        cols = st.columns(5)
        cols[0].metric("Shadow Runs", summary["total_runs"])
        cols[1].metric("Diagnostics", summary["total_diagnostics"])
        cols[2].metric("Unique Markets", summary["unique_markets"])
        cols[3].metric("Latest Created", summary.get("latest_created_at") or "—")
        cols[4].metric("Run Status Keys", len(summary.get("by_run_status") or {}))
        st.caption(f"By Run Status: {summary.get('by_run_status') or {}}")

    st.markdown("#### Recent EMOS Shadow Runs")
    run_rows = _run_rows(list(cast(list[EmosShadowRunRecord], state.get("runs") or [])))
    if run_rows:
        st.dataframe(run_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No EMOS shadow runs loaded.")

    st.markdown("#### Recent EMOS Shadow Diagnostics")
    diagnostic_rows = _diagnostic_rows(list(cast(list[EmosShadowDiagnosticRecord], state.get("diagnostics") or [])))
    if diagnostic_rows:
        st.dataframe(diagnostic_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No EMOS shadow diagnostics loaded.")

    st.markdown("#### Market EMOS Shadow Bundle")
    bundle = cast(EmosShadowMarketBundle | None, state.get("bundle"))
    st.caption(_bundle_summary(bundle))
    if bundle:
        st.dataframe(_run_rows(list(bundle.get("runs") or [])), use_container_width=True, hide_index=True)
        st.dataframe(
            _diagnostic_rows(list(bundle.get("diagnostics") or [])),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("#### Raw JSON State")
    st.json(state.get("raw_state") or {})
