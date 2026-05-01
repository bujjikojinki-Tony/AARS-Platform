from __future__ import annotations

from typing import Any, cast

import streamlit as st

from weather_dashboard.lib.api import apiGet
from weather_dashboard.lib.api import apiPost
from weather_dashboard.types.weather import ShadowEngineEvaluationBundle
from weather_dashboard.types.weather import ShadowEngineEvaluationRecord
from weather_dashboard.types.weather import ShadowEngineEvaluationSummary

STATE_KEY = "pwb05c_shadow_eval_state"
MARKET_KEY = "pwb05c_shadow_eval_market_id"


def build_shadow_engine_evaluation_panel_state() -> dict[str, object]:
    return {
        "summary": None,
        "evaluations": [],
        "bundle": None,
        "message": None,
        "raw_state": {},
    }


def _state() -> dict[str, object]:
    state = st.session_state.get(STATE_KEY)
    if not isinstance(state, dict):
        state = build_shadow_engine_evaluation_panel_state()
        st.session_state[STATE_KEY] = state
    return state


def _set_message(state: dict[str, object], message: str) -> None:
    state["message"] = message


def load_summary(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/shadow-evaluation/summary"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load shadow evaluation summary.")
        return
    state["summary"] = payload.get("summary")
    state["raw_state"] = payload
    _set_message(state, "Shadow evaluation summary loaded.")


def load_evaluations(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/shadow-evaluation/evaluations?limit=50"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load shadow evaluations.")
        return
    state["evaluations"] = list(payload.get("items") or [])
    state["raw_state"] = payload
    _set_message(state, f"Loaded {len(state['evaluations'])} shadow evaluation rows.")


def load_bundle(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    payload = cast(dict[str, Any], apiGet(f"/api/shadow-evaluation/market/{market_id}?limit=100"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load shadow evaluation market bundle.")
        return
    state["bundle"] = payload.get("bundle")
    state["raw_state"] = payload
    _set_message(state, f"Loaded shadow evaluation bundle for {market_id}.")


def build_evaluation(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    payload = cast(dict[str, Any], apiPost("/api/shadow-evaluation/build", {"market_id": market_id}))
    state["raw_state"] = payload
    if payload.get("status") != "ok":
        _set_message(state, str(payload.get("message") or "Shadow evaluation build failed."))
        return
    _set_message(state, f"Built shadow evaluation for {market_id}.")
    load_summary(state)
    load_evaluations(state)


def build_all_evaluations(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiPost("/api/shadow-evaluation/build-all", {}))
    state["raw_state"] = payload
    if payload.get("status") != "ok":
        _set_message(state, str(payload.get("message") or "Build-all shadow evaluation failed."))
        return
    _set_message(state, f"Built {payload.get('built_count', 0)} shadow evaluations.")
    load_summary(state)
    load_evaluations(state)


def _evaluation_rows(items: list[ShadowEngineEvaluationRecord]) -> list[dict[str, object]]:
    return [
        {
            "created_at": item["created_at"],
            "market_id": item["market_id"],
            "primary_probability": item.get("primary_probability"),
            "deb_probability": item.get("deb_probability"),
            "emos_probability": item.get("emos_probability"),
            "actual_outcome_value": item.get("actual_outcome_value"),
            "primary_brier_score": item.get("primary_brier_score"),
            "deb_brier_score": item.get("deb_brier_score"),
            "emos_brier_score": item.get("emos_brier_score"),
            "best_engine": item["best_engine"],
            "evaluation_status": item["evaluation_status"],
        }
        for item in items
    ]


def _bundle_summary(bundle: ShadowEngineEvaluationBundle | None) -> str:
    if not bundle:
        return "No shadow evaluation market bundle loaded."
    return f"Market `{bundle['market_id']}` with {len(bundle.get('evaluations') or [])} evaluation rows."


def render_shadow_engine_evaluation_panel() -> None:
    state = _state()
    st.markdown("### Shadow Engine Evaluation")
    st.caption(
        "Read-only comparison of Gaussian, DEB shadow, and EMOS shadow outputs from accepted historical memory only. No trade, execute, simulate, promote model, auto calibrate, wallet, order, cancel, or go-live controls are exposed."
    )

    st.text_input("Market ID", value=st.session_state.get(MARKET_KEY, "tokyo_weather_market"), key=MARKET_KEY)

    action_cols = st.columns(2, gap="small")
    actions = [
        ("Load Summary", load_summary),
        ("Load Evaluation Rows", load_evaluations),
        ("Build Evaluation", build_evaluation),
        ("Build All Eligible", build_all_evaluations),
        ("Load Market Bundle", load_bundle),
    ]
    for idx, (label, fn) in enumerate(actions):
        col = action_cols[idx % 2]
        with col:
            if st.button(label, key=f"pwb05c_{label.lower().replace(' ', '_')}", use_container_width=True):
                fn(state)

    if state.get("message"):
        st.info(str(state["message"]))

    summary = cast(ShadowEngineEvaluationSummary | None, state.get("summary"))
    if summary:
        cols = st.columns(5)
        cols[0].metric("Evaluations", summary["total_evaluations"])
        cols[1].metric("Unique Markets", summary["unique_markets"])
        cols[2].metric("Status Keys", len(summary.get("by_status") or {}))
        cols[3].metric("Best Engine Keys", len(summary.get("by_best_engine") or {}))
        cols[4].metric("Latest Created", summary.get("latest_created_at") or "—")
        st.caption(f"By Status: {summary.get('by_status') or {}}")
        st.caption(f"By Best Engine: {summary.get('by_best_engine') or {}}")

    st.markdown("#### Recent Shadow Evaluation Rows")
    rows = _evaluation_rows(list(cast(list[ShadowEngineEvaluationRecord], state.get("evaluations") or [])))
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No shadow evaluation rows loaded.")

    st.markdown("#### Market Shadow Evaluation Bundle")
    bundle = cast(ShadowEngineEvaluationBundle | None, state.get("bundle"))
    st.caption(_bundle_summary(bundle))
    if bundle:
        st.dataframe(
            _evaluation_rows(list(bundle.get("evaluations") or [])),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("#### Raw JSON State")
    st.json(state.get("raw_state") or {})
