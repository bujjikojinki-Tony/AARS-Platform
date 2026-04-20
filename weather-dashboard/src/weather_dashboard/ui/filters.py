import streamlit as st
import pandas as pd


def render_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.subheader("Filters")

    if df.empty:
        st.info("No rows available.")
        return df

    working = df.copy()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if "location_name" in working.columns:
            locations = ["All"] + sorted(working["location_name"].dropna().unique().tolist())
            selected_location = st.selectbox("Location", locations)
            if selected_location != "All":
                working = working[working["location_name"] == selected_location]

    with col2:
        if "comparison_status" in working.columns:
            statuses = ["All"] + sorted(working["comparison_status"].dropna().unique().tolist())
            selected_status = st.selectbox("Comparison Status", statuses)
            if selected_status != "All":
                working = working[working["comparison_status"] == selected_status]

    with col3:
        max_gap = (
            float(working["confidence_adjusted_gap"].max())
            if "confidence_adjusted_gap" in working.columns and not working.empty
            else 0.0
        )
        selected_gap = st.slider(
            "Min Adjusted Gap",
            min_value=0.0,
            max_value=max(max_gap, 1.0),
            value=0.0,
            step=0.1,
        )
        if "confidence_adjusted_gap" in working.columns:
            working = working[working["confidence_adjusted_gap"] >= selected_gap]

    with col4:
        selected_conf = st.slider(
            "Min Confidence",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.05,
        )
        if "confidence_score" in working.columns:
            working = working[working["confidence_score"] >= selected_conf]

    st.caption(f"Filtered rows: {len(working)}")
    return working

