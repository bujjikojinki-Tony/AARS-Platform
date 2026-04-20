import streamlit as st
import pandas as pd


def render_timeseries_panel(df: pd.DataFrame, selected_market_id: str | None) -> None:
    st.subheader("Time Series")

    if df.empty:
        st.info("No timeseries data available.")
        return

    if selected_market_id:
        df = df[df["market_id"] == selected_market_id]

    if df.empty:
        st.info("No timeseries rows for selected market.")
        return

    working = df.copy()

    if "timestamp" in working.columns:
        working["timestamp"] = pd.to_datetime(working["timestamp"])

    st.caption(f"Selected market: {selected_market_id or 'All'}")

    col1, col2 = st.columns(2)

    with col1:
        if {"timestamp", "model_value"}.issubset(working.columns):
            chart_df = working[["timestamp", "model_value"]].set_index("timestamp")
            st.write("Model Value")
            st.line_chart(chart_df, use_container_width=True)

    with col2:
        if {"timestamp", "confidence_adjusted_gap"}.issubset(working.columns):
            chart_df = working[["timestamp", "confidence_adjusted_gap"]].set_index("timestamp")
            st.write("Confidence Adjusted Gap")
            st.line_chart(chart_df, use_container_width=True)

    if {"timestamp", "market_probability"}.issubset(working.columns):
        chart_df = working[["timestamp", "market_probability"]].set_index("timestamp")
        st.write("Market Probability")
        st.line_chart(chart_df, use_container_width=True)
