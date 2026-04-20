from __future__ import annotations

import pandas as pd
import streamlit as st


def render_history_relationship_panel(
    history_df: pd.DataFrame,
    selected_market_id: str | None,
) -> None:
    st.subheader("History / Odds Relationship")

    if history_df.empty:
        st.info("No comparison history available.")
        return

    if not selected_market_id:
        st.info("Select a market to inspect history relationship.")
        return

    working = history_df[history_df["market_id"] == selected_market_id].copy()
    if working.empty:
        st.info("No historical rows for selected market.")
        return

    working["timestamp"] = pd.to_datetime(working["timestamp"], errors="coerce")
    working = working.sort_values(by="timestamp")

    cols = ["timestamp", "market_probability", "confidence_adjusted_gap", "comparison_status", "model_band", "market_band"]
    existing = [column for column in cols if column in working.columns]
    preview = working[existing].copy()

    numeric_cols = [column for column in ["market_probability", "confidence_adjusted_gap"] if column in working.columns]

    if numeric_cols:
        chart_df = working[["timestamp", *numeric_cols]].set_index("timestamp")
        st.line_chart(chart_df, use_container_width=True)

        scatter_df = working[[*numeric_cols]].dropna()
        if len(scatter_df) >= 2 and len(numeric_cols) == 2:
            st.caption("Odds vs history gap scatter")
            st.scatter_chart(scatter_df, x=numeric_cols[0], y=numeric_cols[1], use_container_width=True)

            corr = scatter_df[numeric_cols[0]].corr(scatter_df[numeric_cols[1]])
            if pd.notna(corr):
                st.metric("Odds / Gap Correlation", f"{corr:.2f}")
        elif len(numeric_cols) == 2:
            st.info("Need at least two historical rows to draw odds/gap relationship.")
    else:
        st.info("No odds columns found in history.")

    with st.expander("Historical rows", expanded=False):
        st.dataframe(preview, use_container_width=True, hide_index=True)
