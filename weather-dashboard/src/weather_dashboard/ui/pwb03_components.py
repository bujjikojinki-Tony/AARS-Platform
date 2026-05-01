from __future__ import annotations

from typing import cast

import streamlit as st

from weather_dashboard.lib.api import apiGet
from weather_dashboard.lib.api import apiPost
from weather_dashboard.types.weather import CalibrationResult
from weather_dashboard.types.weather import ProbabilityComparison
from weather_dashboard.types.weather import ProbabilityEngineConfig
from weather_dashboard.types.weather import WorkstationPayload
from weather_dashboard.ui.status_badge import render_status_badge


def render_probability_comparison_panel(comparison: ProbabilityComparison | None, *, on_compare=None) -> None:
    st.markdown("### Probability Comparison")
    if not comparison:
        st.info("No comparison found. Run comparison after a WeatherView exists.")
        if on_compare:
            st.button("Run Compare", on_click=on_compare, use_container_width=True)
        return
    st.caption("Active probability remains governed by the accepted PRIMARY engine.")
    badge_cols = st.columns([1, 1, 2])
    with badge_cols[0]:
        render_status_badge(f"Active: {comparison['active_engine_id']}")
    with badge_cols[1]:
        render_status_badge(f"Disagreement: {comparison['disagreement_level']}")
    with badge_cols[2]:
        if on_compare:
            st.button("Re-run Compare", on_click=on_compare, use_container_width=True)
    metric_cols = st.columns(4)
    metric_cols[0].metric("Active Probability", f"{comparison['active_probability'] * 100:.1f}%")
    metric_cols[1].metric("Engine Spread", f"{comparison['spread_between_engines'] * 100:.2f}%")
    metric_cols[2].metric("Weather View", comparison["weather_view_id"])
    metric_cols[3].metric("Created", comparison["created_at"])
    st.dataframe(
        [
            {
                "Engine": run["engine_id"],
                "Type": run["engine_type"],
                "Probability": f"{run['model_probability'] * 100:.1f}%",
                "Expected": run.get("expected_value", "—"),
                "Sigma": run.get("sigma", "—"),
                "Warnings": "; ".join(run.get("warnings") or []) or "—",
            }
            for run in comparison["engine_runs"]
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.markdown(f"**Selection reason:** {comparison['selection_reason']}")
    if comparison.get("warnings"):
        st.warning("\n".join(comparison["warnings"]))


def render_calibration_history_panel() -> None:
    st.markdown("### Calibration History")
    st.caption("Review Brier score, absolute error, and probability buckets by engine or market.")
    engine_id = st.text_input("Engine ID", value=st.session_state.get("pwb03_calibration_engine_id", "gaussian_v0"))
    market_id = st.text_input("Market ID", value=st.session_state.get("pwb03_calibration_market_id", "mock_weather_strong_yes"))
    st.session_state["pwb03_calibration_engine_id"] = engine_id
    st.session_state["pwb03_calibration_market_id"] = market_id

    col_a, col_b, col_c, col_d = st.columns(4)

    def _load_by_engine() -> None:
        res = apiGet(f"/api/probability/calibration/{engine_id}")
        st.session_state["pwb03_calibration_items"] = res.get("results") or []

    def _load_by_market() -> None:
        res = apiGet(f"/api/probability/calibration/market/{market_id}")
        st.session_state["pwb03_calibration_items"] = res.get("results") or []

    def _record_hit() -> None:
        apiPost(
            "/api/probability/outcomes",
            {
                "market_id": market_id,
                "status": "RESOLVED",
                "resolved_direction_hit": True,
                "resolved_value": 31.8,
                "official_source": "manual_ui",
                "notes": "Manual positive outcome from calibration panel.",
            },
        )
        st.session_state["pwb03_calibration_message"] = "Manual RESOLVED outcome recorded."

    def _calibrate() -> None:
        res = apiPost(f"/api/probability/calibrate/{market_id}")
        if res.get("status") != "ok":
            st.session_state["pwb03_calibration_message"] = (
                res.get("message") or "Calibration failed. Ensure outcome is RESOLVED and comparison runs exist."
            )
            return
        st.session_state["pwb03_calibration_items"] = res.get("results") or []
        st.session_state["pwb03_calibration_message"] = "Calibration results created."

    col_a.button("Load by Engine", use_container_width=True, on_click=_load_by_engine)
    col_b.button("Load by Market", use_container_width=True, on_click=_load_by_market)
    col_c.button("Record Hit", use_container_width=True, on_click=_record_hit)
    col_d.button("Calibrate", use_container_width=True, on_click=_calibrate)

    if st.session_state.get("pwb03_calibration_message"):
        st.info(str(st.session_state["pwb03_calibration_message"]))

    items = cast(list[CalibrationResult], st.session_state.get("pwb03_calibration_items") or [])
    st.dataframe(
        [
            {
                "Engine": item["engine_id"],
                "Market": item["market_id"],
                "Predicted": f"{item['predicted_probability'] * 100:.1f}%",
                "Actual": "HIT" if item["actual_outcome"] == 1 else "MISS",
                "Brier": f"{item['brier_score']:.4f}",
                "Abs Error": f"{item['absolute_error']:.4f}",
                "Bucket": item.get("bucket") or "—",
                "Created": item["created_at"],
            }
            for item in items
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_probability_engine_registry_table() -> None:
    st.markdown("### Probability Engine Registry")
    st.caption("Active and shadow probability engines. Shadow engines cannot drive trading.")
    if st.button("Load Engines", use_container_width=True):
        st.session_state["pwb03_engines_payload"] = apiGet("/api/probability/engines")
    payload = cast(dict | None, st.session_state.get("pwb03_engines_payload"))
    if not payload:
        st.info("No engines loaded.")
        return

    engines = cast(list[ProbabilityEngineConfig], payload.get("engines") or [])
    st.dataframe(
        [
            {
                "Engine": engine["engine_id"],
                "Type": engine["engine_type"],
                "Enabled": "YES" if engine["enabled"] else "NO",
                "Can Be Primary": "YES" if engine["can_be_primary"] else "NO",
                "Version": engine["version"],
                "Description": engine.get("description") or "—",
            }
            for engine in engines
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"Primary: {(payload.get('primary') or {}).get('engine_id') or '-'}")
    if engines:
        target_engine = st.selectbox("Promotion target", [engine["engine_id"] for engine in engines], key="pwb03_promotion_target")
        if st.button("Evaluate", use_container_width=True):
            result = apiPost(f"/api/probability/promotion/{target_engine}")
            if result.get("status") == "ok" and result.get("decision"):
                decision = result["decision"]
                st.session_state["pwb03_engine_registry_message"] = (
                    f"{decision['engine_id']}: {decision['decision']} — {decision['reason']}"
                )
            else:
                st.session_state["pwb03_engine_registry_message"] = result.get("message") or "Promotion evaluation failed."
    if st.session_state.get("pwb03_engine_registry_message"):
        st.info(str(st.session_state["pwb03_engine_registry_message"]))
