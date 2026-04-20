import streamlit as st
import pandas as pd


def render_bias_summary_panel(df: pd.DataFrame) -> None:
    st.subheader("Bias Report Summary")

    if df.empty:
        st.info("No bias report available.")
        return

    # 兼容 summary csv 的 metric/value 结构
    if {"metric", "value"}.issubset(df.columns):
        metrics = dict(zip(df["metric"], df["value"]))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("MAE", metrics.get("mae", "-"))
        c2.metric("RMSE", metrics.get("rmse", "-"))
        c3.metric("Band Hit Rate", metrics.get("band_hit_rate", "-"))
        c4.metric("Avg Drift Span", metrics.get("avg_drift_span", "-"))

        c5, c6 = st.columns(2)
        c5.metric("Stable Groups Count", metrics.get("stable_groups_count", "-"))
        c6.metric("Extreme Miss Rate", metrics.get("extreme_miss_rate", "-"))

        with st.expander("Raw Bias Metrics", expanded=False):
            st.dataframe(df, use_container_width=True, hide_index=True)

    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

