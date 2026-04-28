import streamlit as st
import pandas as pd


def render_timeline_panel(
    df: pd.DataFrame,
    selected_market_id: str | None,
    *,
    top_parameter_view: dict | None = None,
) -> None:
    st.subheader("Market Drill-down Timeline")

    if df.empty:
        st.info("No timeline data available.")
        return

    if not selected_market_id:
        st.info("Select a market to view timeline.")
        return

    working = df[df["market_id"] == selected_market_id].copy()

    if working.empty:
        st.info("No timeline rows for selected market.")
        return

    if "timestamp" in working.columns:
        working["timestamp"] = pd.to_datetime(working["timestamp"])

    if isinstance(top_parameter_view, dict):
        weather = top_parameter_view.get("weather") if isinstance(top_parameter_view.get("weather"), dict) else {}
        source_contract = (
            top_parameter_view.get("source_contract")
            if isinstance(top_parameter_view.get("source_contract"), dict)
            else {}
        )
        decision = top_parameter_view.get("decision") if isinstance(top_parameter_view.get("decision"), dict) else {}
        with st.container(border=True):
            st.caption("Top Parameter Surface")
            cols_top = st.columns(4)
            with cols_top[0]:
                st.metric("Market", str(top_parameter_view.get("market_family") or "-"), help=str(top_parameter_view.get("market_question") or "-"))
                st.caption(str(top_parameter_view.get("market_id") or "-"))
            with cols_top[1]:
                st.metric("Weather", str(weather.get("forecast_value") or weather.get("observation_value") or "-"))
                st.caption(str(weather.get("station_id") or "-"))
            with cols_top[2]:
                st.metric("Source", str(source_contract.get("source_match_grade") or "-"))
                st.caption(str(source_contract.get("freshness_status") or "-"))
            with cols_top[3]:
                st.metric("Decision", str(decision.get("can_execute") or "-"))
                st.caption(str(decision.get("primary_block_reason") or "-"))

    cols = [
        c
        for c in [
            "timestamp",
            "market_id",
            "comparison_status",
            "band_distance",
            "confidence_score",
            "confidence_adjusted_gap",
        ]
        if c in working.columns
    ]

    preview = working.sort_values(by="timestamp", ascending=False)[cols]
    st.caption("Showing the latest 5 timeline rows by default. Enable full rows only when auditing history.")
    st.dataframe(
        preview.head(5),
        use_container_width=True,
        hide_index=True,
    )
    if len(preview) > 5 and st.checkbox(
        "Show full timeline rows",
        value=False,
        key=f"timeline_show_full_{selected_market_id}",
    ):
        st.dataframe(
            preview,
            use_container_width=True,
            hide_index=True,
        )
