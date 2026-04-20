from __future__ import annotations

import pandas as pd
import streamlit as st


def render_overview(df: pd.DataFrame) -> None:
    st.subheader("Overview")

    if df.empty:
        st.info("No dashboard rows found.")
        return

    total_rows = len(df)
    strong_div = int((df["comparison_status"] == "strong_divergence").sum()) \
        if "comparison_status" in df.columns else 0
    aligned = int((df["comparison_status"] == "aligned").sum()) \
        if "comparison_status" in df.columns else 0
    avg_gap = float(df["confidence_adjusted_gap"].mean()) \
        if "confidence_adjusted_gap" in df.columns else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", total_rows)
    c2.metric("Strong Divergence", strong_div)
    c3.metric("Aligned", aligned)
    c4.metric("Avg Adj Gap", f"{avg_gap:.2f}")
