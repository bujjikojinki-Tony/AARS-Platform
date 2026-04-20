import pandas as pd
import streamlit as st


def render_divergence_trend_chart(history_df: pd.DataFrame, selected_market_id: str | None) -> None:
    st.subheader("Divergence Trend")

    if history_df.empty:
        st.info("No comparison history available.")
        return

    working = history_df.copy()

    if selected_market_id:
        working = working[working["market_id"] == selected_market_id]

    if working.empty:
        st.info("No history for selected market.")
        return

    working["timestamp"] = pd.to_datetime(working["timestamp"])

    if {"timestamp", "confidence_adjusted_gap"}.issubset(working.columns):
        chart_df = working[["timestamp", "confidence_adjusted_gap"]].set_index("timestamp")
        st.line_chart(chart_df, use_container_width=True)
    else:
        st.info("Missing required columns for divergence trend chart.")
        return
