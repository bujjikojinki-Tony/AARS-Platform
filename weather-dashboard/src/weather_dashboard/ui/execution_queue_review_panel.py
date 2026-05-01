from __future__ import annotations

from typing import Any, cast

import streamlit as st

from weather_dashboard.lib.api import apiGet
from weather_dashboard.lib.api import apiPost
from weather_dashboard.types.weather import ExecutionQueueReviewBundle
from weather_dashboard.types.weather import ExecutionQueueReviewRecord
from weather_dashboard.types.weather import ExecutionQueueReviewSummary

STATE_KEY = "pwb08_execution_queue_review_state"
MARKET_KEY = "pwb08_execution_queue_review_market_id"


def build_execution_queue_review_panel_state() -> dict[str, object]:
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
        state = build_execution_queue_review_panel_state()
        st.session_state[STATE_KEY] = state
    return state


def _set_message(state: dict[str, object], message: str) -> None:
    state["message"] = message


def load_summary(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/execution-queue-review/summary"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load execution queue review summary.")
        return
    state["summary"] = payload.get("summary")
    state["raw_state"] = payload
    _set_message(state, "Execution queue review summary loaded.")


def load_reviews(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/execution-queue-review/reviews?limit=50"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load execution queue reviews.")
        return
    state["reviews"] = list(payload.get("items") or [])
    state["raw_state"] = payload
    _set_message(state, f"Loaded {len(state['reviews'])} execution queue review rows.")


def load_bundle(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    payload = cast(dict[str, Any], apiGet(f"/api/execution-queue-review/market/{market_id}?limit=100"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load execution queue review market bundle.")
        return
    state["bundle"] = payload.get("bundle")
    state["raw_state"] = payload
    _set_message(state, f"Loaded execution queue review bundle for {market_id}.")


def build_review(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    payload = cast(
        dict[str, Any],
        apiPost(
            "/api/execution-queue-review/build",
            {
                "market_id": market_id,
                "execution_decision_review_id": st.session_state.get("pwb08_execution_decision_review_id") or None,
                "metadata": {
                    "ui_action": "build_execution_queue_review",
                },
            },
        ),
    )
    state["raw_state"] = payload
    if payload.get("status") != "ok":
        _set_message(state, str(payload.get("message") or "Execution queue review build failed."))
        return
    _set_message(state, f"Built execution queue review for {market_id}.")
    load_summary(state)
    load_reviews(state)


def build_all_reviews(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiPost("/api/execution-queue-review/build-all", {}))
    state["raw_state"] = payload
    if payload.get("status") != "ok":
        _set_message(state, str(payload.get("message") or "Build-all execution queue review failed."))
        return
    _set_message(state, f"Built {payload.get('built_count', 0)} execution queue review rows.")
    load_summary(state)
    load_reviews(state)


def _review_rows(items: list[ExecutionQueueReviewRecord]) -> list[dict[str, object]]:
    return [
        {
            "reviewed_at": item["reviewed_at"],
            "market_id": item["market_id"],
            "decision_id": item["decision_id"],
            "candidate_id": item["candidate_id"],
            "execution_mode": item.get("execution_mode"),
            "execution_status": item.get("execution_status"),
            "review_status": item["review_status"],
            "approval_status": item["approval_status"],
            "gate_status": item["gate_status"],
            "recommendation": item["recommendation"],
        }
        for item in items
    ]


def _bundle_summary(bundle: ExecutionQueueReviewBundle | None) -> str:
    if not bundle:
        return "No execution queue review bundle loaded."
    return (
        f"Market `{bundle['market_id']}` with "
        f"{len(bundle.get('execution_queue_reviews') or [])} execution queue review rows."
    )


def render_execution_queue_review_panel() -> None:
    state = _state()
    st.markdown("### Execution Queue Review")
    st.caption(
        "Read-only execution queue review from accepted historical evidence only. No trade, execute, simulate, promote model, auto calibrate, wallet, order, cancel, or go-live controls are exposed."
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
            if st.button(label, key=f"pwb08_{label.lower().replace(' ', '_')}", use_container_width=True):
                fn(state)

    if state.get("message"):
        st.info(str(state["message"]))

    summary = cast(ExecutionQueueReviewSummary | None, state.get("summary"))
    if summary:
        cols = st.columns(6)
        cols[0].metric("Queue Reviews", summary["execution_queue_reviews"])
        cols[1].metric("Unique Markets", summary["unique_markets"])
        cols[2].metric("Latest Reviewed", summary.get("latest_reviewed_at") or "—")
        cols[3].metric("Review Status Keys", len(summary.get("by_review_status") or {}))
        cols[4].metric("Approval Status Keys", len(summary.get("by_approval_status") or {}))
        cols[5].metric("Gate Status Keys", len(summary.get("by_gate_status") or {}))
        st.caption(f"By Review Status: {summary.get('by_review_status') or {}}")
        st.caption(f"By Approval Status: {summary.get('by_approval_status') or {}}")
        st.caption(f"By Gate Status: {summary.get('by_gate_status') or {}}")
        st.caption(f"By Execution Status: {summary.get('by_execution_status') or {}}")
        st.caption(f"By Execution Mode: {summary.get('by_execution_mode') or {}}")
    else:
        st.caption("No execution queue review summary loaded.")

    st.markdown("#### Recent Execution Queue Reviews")
    review_rows = _review_rows(list(cast(list[ExecutionQueueReviewRecord], state.get("reviews") or [])))
    if review_rows:
        st.dataframe(review_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No execution queue reviews loaded.")

    st.markdown("#### Market Execution Queue Review Bundle")
    bundle = cast(ExecutionQueueReviewBundle | None, state.get("bundle"))
    st.caption(_bundle_summary(bundle))
    if bundle:
        st.dataframe(
            _review_rows(list(bundle.get("execution_queue_reviews") or [])),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("#### Raw JSON State")
    st.json(state.get("raw_state") or {})
