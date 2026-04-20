import streamlit as st
import pandas as pd


def render_timeline_panel(df: pd.DataFrame, selected_market_id: str | None) -> None:
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
