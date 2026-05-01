from __future__ import annotations

from typing import Any, cast

import streamlit as st

from weather_dashboard.lib.api import apiGet
from weather_dashboard.lib.api import apiPost
from weather_dashboard.types.weather import BacktestMemoryRecord
from weather_dashboard.types.weather import CalibrationMemoryBundle
from weather_dashboard.types.weather import CalibrationMemorySummary
from weather_dashboard.types.weather import CalibrationSample

STATE_KEY = "pwb05_calibration_memory_state"
MARKET_KEY = "pwb05_market_id"


def build_calibration_memory_panel_state() -> dict[str, object]:
    return {
        "summary": None,
        "eligibility": None,
        "samples": [],
        "backtests": [],
        "bundle": None,
        "message": None,
        "raw_state": {},
    }


def _state() -> dict[str, object]:
    state = st.session_state.get(STATE_KEY)
    if not isinstance(state, dict):
        state = build_calibration_memory_panel_state()
        st.session_state[STATE_KEY] = state
    return state


def _set_message(state: dict[str, object], message: str) -> None:
    state["message"] = message


def load_summary(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/calibration-memory/summary"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load calibration memory summary.")
        return
    state["summary"] = payload.get("summary")
    state["raw_state"] = payload
    _set_message(state, "Calibration memory summary loaded.")


def check_eligibility(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    payload = cast(dict[str, Any], apiGet(f"/api/calibration-memory/eligibility/{market_id}"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to check eligibility.")
        return
    state["eligibility"] = payload.get("eligibility")
    state["raw_state"] = payload
    _set_message(state, f"Eligibility loaded for {market_id}.")


def load_recent_samples(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/calibration-memory/samples?limit=50"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load recent calibration samples.")
        return
    state["samples"] = list(payload.get("items") or [])
    state["raw_state"] = payload
    _set_message(state, f"Loaded {len(state['samples'])} calibration samples.")


def load_recent_backtests(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/calibration-memory/backtests?limit=50"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load recent backtest memory records.")
        return
    state["backtests"] = list(payload.get("items") or [])
    state["raw_state"] = payload
    _set_message(state, f"Loaded {len(state['backtests'])} backtest memory records.")


def load_market_bundle(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    payload = cast(dict[str, Any], apiGet(f"/api/calibration-memory/market/{market_id}?limit=100"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load market calibration memory bundle.")
        return
    state["bundle"] = payload.get("bundle")
    state["raw_state"] = payload
    _set_message(state, f"Loaded calibration memory bundle for {market_id}.")


def build_sample(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    payload = cast(dict[str, Any], apiPost("/api/calibration-memory/build-sample", {"market_id": market_id}))
    state["raw_state"] = payload
    if payload.get("status") != "ok":
        _set_message(state, str(payload.get("message") or "Build calibration sample failed."))
        return
    _set_message(state, f"Built calibration sample for {market_id}.")
    load_summary(state)
    load_recent_samples(state)


def build_backtest(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    payload = cast(
        dict[str, Any],
        apiPost(
            "/api/calibration-memory/build-backtest",
            {"market_id": market_id, "edge_threshold": st.session_state.get("pwb05_edge_threshold", 0.05)},
        ),
    )
    state["raw_state"] = payload
    if payload.get("status") != "ok":
        _set_message(state, str(payload.get("message") or "Build backtest memory failed."))
        return
    _set_message(state, f"Built backtest memory for {market_id}.")
    load_summary(state)
    load_recent_backtests(state)


def build_all_eligible(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiPost("/api/calibration-memory/build-all-eligible", {}))
    state["raw_state"] = payload
    if payload.get("status") != "ok":
        _set_message(state, str(payload.get("message") or "Build-all-eligible failed."))
        return
    _set_message(state, f"Built {payload.get('built_count', 0)} eligible calibration samples.")
    load_summary(state)
    load_recent_samples(state)


def _sample_rows(items: list[CalibrationSample]) -> list[dict[str, object]]:
    return [
        {
            "sampled_at": item["sampled_at"],
            "market_id": item["market_id"],
            "engine_id": item.get("engine_id"),
            "market_probability": item.get("market_probability"),
            "model_probability": item.get("model_probability"),
            "resolved_outcome": item["resolved_outcome"],
            "model_brier_score": item.get("model_brier_score"),
            "market_brier_score": item.get("market_brier_score"),
            "model_beats_market": item.get("model_beats_market"),
            "sample_status": item["sample_status"],
        }
        for item in items
    ]


def _backtest_rows(items: list[BacktestMemoryRecord]) -> list[dict[str, object]]:
    return [
        {
            "sampled_at": item["sampled_at"],
            "market_id": item["market_id"],
            "edge": item.get("edge"),
            "edge_threshold": item.get("edge_threshold"),
            "hypothetical_action": item["hypothetical_action"],
            "hypothetical_result": item["hypothetical_result"],
            "backtest_status": item["backtest_status"],
        }
        for item in items
    ]


def render_calibration_memory_panel() -> None:
    state = _state()
    st.markdown("### Calibration Memory")
    st.caption(
        "Read-only sample and backtest-memory assembly from existing archived records only. No trade, execute, simulate, promote model, auto calibrate, wallet, order, cancel, or go-live controls are exposed."
    )

    st.text_input("Market ID", value=st.session_state.get(MARKET_KEY, "tokyo_weather_market"), key=MARKET_KEY)
    st.number_input("Edge Threshold", min_value=0.0, value=0.05, step=0.01, key="pwb05_edge_threshold")

    action_cols = st.columns(4, gap="small")
    action_rows = [
        ("Load Summary", load_summary),
        ("Check Eligibility", check_eligibility),
        ("Build Calibration Sample", build_sample),
        ("Build Backtest Memory", build_backtest),
        ("Build All Eligible Samples", build_all_eligible),
        ("Load Recent Samples", load_recent_samples),
        ("Load Recent Backtests", load_recent_backtests),
        ("Load Market Bundle", load_market_bundle),
    ]
    for idx, (label, fn) in enumerate(action_rows):
        col = action_cols[idx % 4]
        with col:
            if st.button(label, key=f"pwb05_{label.lower().replace(' ', '_')}", use_container_width=True):
                fn(state)

    if state.get("message"):
        st.info(str(state["message"]))

    summary = cast(CalibrationMemorySummary | None, state.get("summary"))
    if summary:
        cols = st.columns(5)
        cols[0].metric("Calibration Samples", summary["calibration_samples"])
        cols[1].metric("Backtest Memory", summary["backtest_memory_records"])
        cols[2].metric("Unique Markets", summary["unique_markets"])
        cols[3].metric("Latest Sampled", summary.get("latest_sampled_at") or "—")
        cols[4].metric("Eligibility Keys", len(summary.get("by_eligibility") or {}))
        st.caption(f"By Sample Status: {summary.get('by_sample_status') or {}}")
        st.caption(f"By Backtest Status: {summary.get('by_backtest_status') or {}}")
        st.caption(f"By Eligibility: {summary.get('by_eligibility') or {}}")

    eligibility = state.get("eligibility")
    st.markdown("#### Eligibility")
    if eligibility:
        st.json(eligibility)
    else:
        st.caption("No eligibility state loaded.")

    st.markdown("#### Recent Calibration Samples")
    sample_rows = _sample_rows(list(cast(list[CalibrationSample], state.get("samples") or [])))
    if sample_rows:
        st.dataframe(sample_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No calibration samples loaded.")

    st.markdown("#### Recent Backtest Memory Records")
    backtest_rows = _backtest_rows(list(cast(list[BacktestMemoryRecord], state.get("backtests") or [])))
    if backtest_rows:
        st.dataframe(backtest_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No backtest memory records loaded.")

    st.markdown("#### Market Calibration Memory Bundle")
    bundle = cast(CalibrationMemoryBundle | None, state.get("bundle"))
    if bundle:
        st.caption(
            f"Market `{bundle['market_id']}` with "
            f"{len(bundle.get('calibration_samples') or [])} calibration samples and "
            f"{len(bundle.get('backtest_memory_records') or [])} backtest memory records."
        )
        st.dataframe(
            _sample_rows(list(bundle.get("calibration_samples") or [])),
            use_container_width=True,
            hide_index=True,
        )
        st.dataframe(
            _backtest_rows(list(bundle.get("backtest_memory_records") or [])),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No market bundle loaded.")

    st.markdown("#### Raw JSON State")
    st.json(state.get("raw_state") or {})
