from __future__ import annotations

from typing import Any, cast

import streamlit as st

from weather_dashboard.lib.api import apiGet
from weather_dashboard.lib.api import apiPost
from weather_dashboard.types.weather import ActivationReadinessReviewBundle
from weather_dashboard.types.weather import ActivationReadinessReviewRecord
from weather_dashboard.types.weather import ActivationReadinessReviewSummary

STATE_KEY = "pwb10_activation_readiness_review_state"
MARKET_KEY = "pwb10_activation_readiness_review_market_id"


def build_activation_readiness_review_panel_state() -> dict[str, object]:
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
        state = build_activation_readiness_review_panel_state()
        st.session_state[STATE_KEY] = state
    return state


def _set_message(state: dict[str, object], message: str) -> None:
    state["message"] = message


def load_summary(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/activation-readiness-review/summary"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load activation readiness review summary.")
        return
    state["summary"] = payload.get("summary")
    state["raw_state"] = payload
    _set_message(state, "Activation readiness review summary loaded.")


def load_reviews(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiGet("/api/activation-readiness-review/reviews?limit=50"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load activation readiness reviews.")
        return
    state["reviews"] = list(payload.get("items") or [])
    state["raw_state"] = payload
    _set_message(state, f"Loaded {len(state['reviews'])} activation readiness review rows.")


def load_bundle(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    payload = cast(dict[str, Any], apiGet(f"/api/activation-readiness-review/market/{market_id}?limit=100"))
    if payload.get("status") != "ok":
        _set_message(state, "Failed to load activation readiness review market bundle.")
        return
    state["bundle"] = payload.get("bundle")
    state["raw_state"] = payload
    _set_message(state, f"Loaded activation readiness review bundle for {market_id}.")


def build_review(state: dict[str, object]) -> None:
    market_id = str(st.session_state.get(MARKET_KEY, "")).strip()
    if not market_id:
        _set_message(state, "Market ID is required.")
        return
    payload = cast(
        dict[str, Any],
        apiPost(
            "/api/activation-readiness-review/build",
            {
                "market_id": market_id,
                "approval_window_review_id": st.session_state.get("pwb10_approval_window_review_id") or None,
                "metadata": {
                    "ui_action": "build_activation_readiness_review",
                },
            },
        ),
    )
    state["raw_state"] = payload
    if payload.get("status") != "ok":
        _set_message(state, str(payload.get("message") or "Activation readiness review build failed."))
        return
    _set_message(state, f"Built activation readiness review for {market_id}.")
    load_summary(state)
    load_reviews(state)


def build_all_reviews(state: dict[str, object]) -> None:
    payload = cast(dict[str, Any], apiPost("/api/activation-readiness-review/build-all", {}))
    state["raw_state"] = payload
    if payload.get("status") != "ok":
        _set_message(state, str(payload.get("message") or "Build-all activation readiness review failed."))
        return
    _set_message(state, f"Built {payload.get('built_count', 0)} activation readiness review rows.")
    load_summary(state)
    load_reviews(state)


def _review_rows(items: list[ActivationReadinessReviewRecord]) -> list[dict[str, object]]:
    return [
        {
            "reviewed_at": item["reviewed_at"],
            "market_id": item["market_id"],
            "decision_id": item["decision_id"],
            "candidate_id": item["candidate_id"],
            "approval_status": item.get("approval_status"),
            "window_state": item.get("window_state"),
            "review_status": item.get("review_status"),
            "readiness_status": item["readiness_status"],
            "recommendation": item["recommendation"],
        }
        for item in items
    ]


def _bundle_summary(bundle: ActivationReadinessReviewBundle | None) -> str:
    if not bundle:
        return "No activation readiness review bundle loaded."
    return (
        f"Market `{bundle['market_id']}` with "
        f"{len(bundle.get('activation_readiness_reviews') or [])} activation readiness review rows."
    )


def render_activation_readiness_review_panel() -> None:
    state = _state()
    st.markdown("### Activation Readiness Review")
    st.caption(
        "Read-only activation-readiness review from accepted historical evidence only. No trade, execute, simulate, promote model, auto calibrate, wallet, order, cancel, or go-live controls are exposed."
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
            if st.button(label, key=f"pwb10_{label.lower().replace(' ', '_')}", use_container_width=True):
                fn(state)

    if state.get("message"):
        st.info(str(state["message"]))

    summary = cast(ActivationReadinessReviewSummary | None, state.get("summary"))
    if summary:
        cols = st.columns(5)
        cols[0].metric("Readiness Reviews", summary["activation_readiness_reviews"])
        cols[1].metric("Unique Markets", summary["unique_markets"])
        cols[2].metric("Latest Reviewed", summary.get("latest_reviewed_at") or "—")
        cols[3].metric("Readiness Keys", len(summary.get("by_readiness_status") or {}))
        cols[4].metric("Recommendation Keys", len(summary.get("by_recommendation") or {}))
        st.caption(f"By Readiness Status: {summary.get('by_readiness_status') or {}}")
        st.caption(f"By Recommendation: {summary.get('by_recommendation') or {}}")
        st.caption(f"By Approval Status: {summary.get('by_approval_status') or {}}")
    else:
        st.caption("No activation readiness review summary loaded.")

    st.markdown("#### Recent Activation Readiness Reviews")
    review_rows = _review_rows(list(cast(list[ActivationReadinessReviewRecord], state.get("reviews") or [])))
    if review_rows:
        st.dataframe(review_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No activation readiness reviews loaded.")

    st.markdown("#### Market Activation Readiness Review Bundle")
    bundle = cast(ActivationReadinessReviewBundle | None, state.get("bundle"))
    st.caption(_bundle_summary(bundle))
    if bundle:
        st.dataframe(
            _review_rows(list(bundle.get("activation_readiness_reviews") or [])),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("#### Raw JSON State")
    st.json(state.get("raw_state") or {})
