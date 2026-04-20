from __future__ import annotations

import pandas as pd
import streamlit as st


def render_comparison_table(df: pd.DataFrame) -> None:
    st.subheader("Comparison Table")

    if df.empty:
        st.info("No comparison rows available.")
        return

    display_cols = [
        "market_id",
        "market_question",
        "location_name",
        "target_date",
        "variable_name",
        "favored_side",
        "market_probability",
        "yes_price",
        "no_price",
        "model_value",
        "model_band",
        "market_band",
        "band_scheme",
        "market_band_scheme",
        "forecast_market_id",
        "rule_status",
        "rule_market_id",
        "market_family",
        "resolution_scope",
        "supported_by_current_pipeline",
        "required_data_source",
        "band_distance",
        "confidence_score",
        "confidence_adjusted_gap",
        "comparison_status",
        "action_hint",
        "market_snapshot_ref",
        "forecast_snapshot_ref",
        "comparison_reason",
    ]

    existing = [c for c in display_cols if c in df.columns]
    st.dataframe(df[existing], use_container_width=True, hide_index=True)
