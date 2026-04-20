import streamlit as st
import pandas as pd


def render_divergence_chart(df: pd.DataFrame) -> None:
    st.subheader("Divergence Chart")

    if df.empty:
        st.info("No data for divergence chart.")
        return

    required = {"location_name", "confidence_adjusted_gap"}
    if not required.issubset(df.columns):
        st.info("Missing required columns for divergence chart.")
        return

    chart_df = (
        df[["location_name", "confidence_adjusted_gap"]]
        .groupby("location_name", as_index=False)
        .mean()
        .sort_values(by="confidence_adjusted_gap", ascending=False)
    )

    st.bar_chart(
        chart_df.set_index("location_name"),
        use_container_width=True,
    )

