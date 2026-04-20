import streamlit as st
import pandas as pd


def render_timeseries_placeholder(df: pd.DataFrame) -> None:
    st.subheader("Time Series Placeholder")

    if df.empty:
        st.info("No rows available.")
        return

    if "confidence_adjusted_gap" not in df.columns:
        st.info("Missing confidence_adjusted_gap column.")
        return

    # 占位逻辑：用当前表格顺序构造一个“pseudo timeline”
    series_df = pd.DataFrame({
        "step": list(range(1, len(df) + 1)),
        "confidence_adjusted_gap": df["confidence_adjusted_gap"].tolist(),
    }).set_index("step")

    st.line_chart(series_df, use_container_width=True)
    st.caption("Placeholder only. Replace with real Polymarket / forecast time-series later.")

