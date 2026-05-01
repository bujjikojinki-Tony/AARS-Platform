from __future__ import annotations

from typing import Any, cast

import streamlit as st

from weather_dashboard.lib.api import apiGet
from weather_dashboard.lib.api import apiPost
from weather_dashboard.types.weather import CommandReviewBundle
from weather_dashboard.types.weather import CommandReviewRecord
from weather_dashboard.types.weather import CommandReviewSummary
from weather_dashboard.ui.status_badge import render_status_badge

STATE_KEY = "pwb06_command_review_state"
MARKET_KEY = "pwb06_command_review_market_id"
COMMAND_NAME_KEY = "pwb06_command_review_command_name"
SOURCE_PAGE_KEY = "pwb06_command_review_source_page"
TARGET_PAGE_KEY = "pwb06_command_review_target_page"
COMMAND_PATH_KEY = "pwb06_command_review_command_path"


def build_command_review_panel_state() -> dict[str, object]:
    return {
        "summary": None,
        "reviews": [],
        "bundle": None,
        "message": None,
        "raw_state": {},
    }


def _state() -> dict[str, object]:
    state = st.session_state.get(STATE_KEY)
    if not isinstance(state, dict):
        state = build_command_review_panel_state()
        st.session_state[STATE_KEY] = state
    return state


def _set_message(state: dict[str, object], message: str) -> None:
    state["message"] = message


def load_summary(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/command-review/summary"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load command review summary.")
        return
    state["summary"] = payload.get("summary")
    state["raw_state"] = payload
    _set_message(state, "Command review summary loaded.")


def load_reviews(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/command-review/reviews?limit=50"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load command reviews.")
        return
    state["reviews"] = list(payload.get("items") or [])
    state["raw_state"] = payload
    _set_message(state, f"Loaded {len(state['reviews'])} command review rows.")


def load_bundle(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    payload = cast(dict[str, Any], apiGet(f"/api/command-review/market/{market_id}?limit=100"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load command review market bundle.")
        return
    state["bundle"] = payload.get("bundle")
    state["raw_state"] = payload
    _set_message(state, f"Loaded command review bundle for {market_id}.")


def build_review(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    payload = cast(
        dict[str, Any],
        apiPost(
            "/api/command-review/build",
            {
                "market_id": market_id,
                "command_name": st.session_state.get(COMMAND_NAME_KEY) or "/review",
                "source_page": st.session_state.get(SOURCE_PAGE_KEY) or "command",
                "target_page": st.session_state.get(TARGET_PAGE_KEY) or "history",
                "command_path": st.session_state.get(COMMAND_PATH_KEY) or "/api/command-review/build",
                "metadata": {
                    "ui_action": "build_command_review",
                },
            },
        ),
    )
    state["raw_state"] = payload
    if payload.get("status") != "ok":
        _set_message(state, str(payload.get("message") or "Command review build failed."))
        return
    _set_message(state, f"Built command review for {market_id}.")
    load_summary(state)
    load_reviews(state)


def build_all_reviews(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiPost("/api/command-review/build-all", {}))
    state["raw_state"] = payload
    if payload.get("status") != "ok":
        _set_message(state, str(payload.get("message") or "Build-all command review failed."))
        return
    _set_message(state, f"Built {payload.get('built_count', 0)} command review rows.")
    load_summary(state)
    load_reviews(state)


def _review_rows(items: list[CommandReviewRecord]) -> list[dict[str, object]]:
    return [
        {
            "reviewed_at": item["reviewed_at"],
            "market_id": item["market_id"],
            "command_name": item["command_name"],
            "review_status": item["review_status"],
            "approval_status": item["approval_status"],
            "gate_status": item["gate_status"],
            "recommendation": item["recommendation"],
            "execution_mode": item.get("execution_mode"),
            "risk_status": item.get("risk_status"),
            "active_engine_id": item.get("active_engine_id"),
        }
        for item in items
    ]


def _bundle_summary(bundle: CommandReviewBundle | None) -> str:
    if not bundle:
        return "No command review bundle loaded."
    return (
        f"Market `{bundle['market_id']}` with "
        f"{len(bundle.get('command_reviews') or [])} command review rows."
    )


def render_command_review_panel() -> None:
    state = _state()
    st.markdown("### Governed Command Review")
    st.caption(
        "Read-only command review and gate visibility built from accepted historical memory only. No trade, execute, simulate, promote model, auto calibrate, wallet, order, cancel, or go-live controls are exposed."
    )

    top_cols = st.columns(2, gap="small")
    with top_cols[0]:
        st.text_input("Market ID", value=st.session_state.get(MARKET_KEY, "tokyo_weather_market"), key=MARKET_KEY)
    with top_cols[1]:
        st.text_input("Command Name", value=st.session_state.get(COMMAND_NAME_KEY, "/review"), key=COMMAND_NAME_KEY)

    detail_cols = st.columns(3, gap="small")
    with detail_cols[0]:
        st.text_input("Source Page", value=st.session_state.get(SOURCE_PAGE_KEY, "command"), key=SOURCE_PAGE_KEY)
    with detail_cols[1]:
        st.text_input("Target Page", value=st.session_state.get(TARGET_PAGE_KEY, "history"), key=TARGET_PAGE_KEY)
    with detail_cols[2]:
        st.text_input(
            "Command Path",
            value=st.session_state.get(COMMAND_PATH_KEY, "/api/command-review/build"),
            key=COMMAND_PATH_KEY,
        )

    action_cols = st.columns(3, gap="small")
    actions = [
        ("Load Summary", load_summary),
        ("Load Recent Reviews", load_reviews),
        ("Load Market Bundle", load_bundle),
        ("Build Review", build_review),
        ("Build All Eligible", build_all_reviews),
    ]
    for idx, (label, fn) in enumerate(actions):
        col = action_cols[idx % 3]
        with col:
            if st.button(label, key=f"pwb06_{label.lower().replace(' ', '_')}", use_container_width=True):
                fn(state)

    if state.get("message"):
        st.info(str(state["message"]))

    summary = cast(CommandReviewSummary | None, state.get("summary"))
    if summary:
        cols = st.columns(5)
        cols[0].metric("Command Reviews", summary["command_reviews"])
        cols[1].metric("Unique Markets", summary["unique_markets"])
        cols[2].metric("Latest Reviewed", summary.get("latest_reviewed_at") or "—")
        cols[3].metric("Review Status Keys", len(summary.get("by_review_status") or {}))
        cols[4].metric("Gate Status Keys", len(summary.get("by_gate_status") or {}))
        st.caption(f"By Review Status: {summary.get('by_review_status') or {}}")
        st.caption(f"By Approval Status: {summary.get('by_approval_status') or {}}")
        st.caption(f"By Gate Status: {summary.get('by_gate_status') or {}}")
        badge_cols = st.columns(3)
        with badge_cols[0]:
            render_status_badge(f"Review: {summary.get('by_review_status') or {}}")
        with badge_cols[1]:
            render_status_badge(f"Approval: {summary.get('by_approval_status') or {}}")
        with badge_cols[2]:
            render_status_badge(f"Gate: {summary.get('by_gate_status') or {}}")
    else:
        st.caption("No command review summary loaded.")

    st.markdown("#### Recent Command Reviews")
    review_rows = _review_rows(list(cast(list[CommandReviewRecord], state.get("reviews") or [])))
    if review_rows:
        st.dataframe(review_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No command reviews loaded.")

    st.markdown("#### Market Command Review Bundle")
    bundle = cast(CommandReviewBundle | None, state.get("bundle"))
    st.caption(_bundle_summary(bundle))
    if bundle:
        st.dataframe(_review_rows(list(bundle.get("command_reviews") or [])), use_container_width=True, hide_index=True)

    st.markdown("#### Raw JSON State")
    st.json(state.get("raw_state") or {})
    st.markdown(
        '<div style="margin-top:0.75rem; font-size:0.78rem; opacity:0.62;">Created By <a href="https://deerflow.tech" target="_blank" rel="noreferrer">Deerflow</a></div>',
        unsafe_allow_html=True,
    )
