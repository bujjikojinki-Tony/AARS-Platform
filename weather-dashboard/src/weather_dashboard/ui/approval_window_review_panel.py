from __future__ import annotations

from typing import Any, cast

import streamlit as st

from weather_dashboard.lib.api import apiGet
from weather_dashboard.lib.api import apiPost
from weather_dashboard.types.weather import ApprovalWindowReviewBundle
from weather_dashboard.types.weather import ApprovalWindowReviewRecord
from weather_dashboard.types.weather import ApprovalWindowReviewSummary

STATE_KEY = "pwb09_approval_window_review_state"
MARKET_KEY = "pwb09_approval_window_review_market_id"


def build_approval_window_review_panel_state() -> dict[str, object]:
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
        state = build_approval_window_review_panel_state()
        st.session_state[STATE_KEY] = state
    return state


def _set_message(state: dict[str, object], message: str) -> None:
    state["message"] = message


def load_summary(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/approval-window-review/summary"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load approval window review summary.")
        return
    state["summary"] = payload.get("summary")
    state["raw_state"] = payload
    _set_message(state, "Approval window review summary loaded.")


def load_reviews(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/approval-window-review/reviews?limit=50"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load approval window reviews.")
        return
    state["reviews"] = list(payload.get("items") or [])
    state["raw_state"] = payload
    _set_message(state, f"Loaded {len(state['reviews'])} approval window review rows.")


def load_bundle(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    payload = cast(dict[str, Any], apiGet(f"/api/approval-window-review/market/{market_id}?limit=100"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load approval window review market bundle.")
        return
    state["bundle"] = payload.get("bundle")
    state["raw_state"] = payload
    _set_message(state, f"Loaded approval window review bundle for {market_id}.")


def build_review(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    payload = cast(
        dict[str, Any],
        apiPost(
            "/api/approval-window-review/build",
            {
                "market_id": market_id,
                "execution_queue_review_id": st.session_state.get("pwb09_execution_queue_review_id") or None,
                "metadata": {
                    "ui_action": "build_approval_window_review",
                },
            },
        ),
    )
    state["raw_state"] = payload
    if payload.get("status") != "ok":
        _set_message(state, str(payload.get("message") or "Approval window review build failed."))
        return
    _set_message(state, f"Built approval window review for {market_id}.")
    load_summary(state)
    load_reviews(state)


def build_all_reviews(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiPost("/api/approval-window-review/build-all", {}))
    state["raw_state"] = payload
    if payload.get("status") != "ok":
        _set_message(state, str(payload.get("message") or "Build-all approval window review failed."))
        return
    _set_message(state, f"Built {payload.get('built_count', 0)} approval window review rows.")
    load_summary(state)
    load_reviews(state)


def _review_rows(items: list[ApprovalWindowReviewRecord]) -> list[dict[str, object]]:
    return [
        {
            "reviewed_at": item["reviewed_at"],
            "market_id": item["market_id"],
            "decision_id": item["decision_id"],
            "candidate_id": item["candidate_id"],
            "approval_status": item.get("approval_status"),
            "approval_window_valid": item.get("approval_window_valid"),
            "approval_valid_until": item.get("approval_valid_until"),
            "review_status": item["review_status"],
            "window_state": item["window_state"],
            "recommendation": item["recommendation"],
        }
        for item in items
    ]


def _bundle_summary(bundle: ApprovalWindowReviewBundle | None) -> str:
    if not bundle:
        return "No approval window review bundle loaded."
    return (
        f"Market `{bundle['market_id']}` with "
        f"{len(bundle.get('approval_window_reviews') or [])} approval window review rows."
    )


def render_approval_window_review_panel() -> None:
    state = _state()
    st.markdown("### Approval Window Review")
    st.caption(
        "Read-only approval-window review from accepted historical evidence only. No trade, execute, simulate, promote model, auto calibrate, wallet, order, cancel, or go-live controls are exposed."
    )

    st.text_input("Market ID", value=st.session_state.get(MARKET_KEY, "tokyo_weather_market"), key=MARKET_KEY)

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
            if st.button(label, key=f"pwb09_{label.lower().replace(' ', '_')}", use_container_width=True):
                fn(state)

    if state.get("message"):
        st.info(str(state["message"]))

    summary = cast(ApprovalWindowReviewSummary | None, state.get("summary"))
    if summary:
        cols = st.columns(5)
        cols[0].metric("Approval Reviews", summary["approval_window_reviews"])
        cols[1].metric("Unique Markets", summary["unique_markets"])
        cols[2].metric("Latest Reviewed", summary.get("latest_reviewed_at") or "—")
        cols[3].metric("Review Status Keys", len(summary.get("by_review_status") or {}))
        cols[4].metric("Window State Keys", len(summary.get("by_window_state") or {}))
        st.caption(f"By Review Status: {summary.get('by_review_status') or {}}")
        st.caption(f"By Window State: {summary.get('by_window_state') or {}}")
        st.caption(f"By Approval Status: {summary.get('by_approval_status') or {}}")
    else:
        st.caption("No approval window review summary loaded.")

    st.markdown("#### Recent Approval Window Reviews")
    review_rows = _review_rows(list(cast(list[ApprovalWindowReviewRecord], state.get("reviews") or [])))
    if review_rows:
        st.dataframe(review_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No approval window reviews loaded.")

    st.markdown("#### Market Approval Window Review Bundle")
    bundle = cast(ApprovalWindowReviewBundle | None, state.get("bundle"))
    st.caption(_bundle_summary(bundle))
    if bundle:
        st.dataframe(
            _review_rows(list(bundle.get("approval_window_reviews") or [])),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("#### Raw JSON State")
    st.json(state.get("raw_state") or {})
