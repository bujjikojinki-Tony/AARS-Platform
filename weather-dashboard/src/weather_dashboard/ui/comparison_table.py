from __future__ import annotations

import pandas as pd
import streamlit as st


def render_comparison_table(df: pd.DataFrame) -> None:
    st.subheader("Comparison Table")

    if df.empty:
        st.info("No comparison rows available.")
        return

    top_parameter_view = None
    if "top_parameter_view" in df.columns:
        candidate = df.iloc[0].get("top_parameter_view")
        if isinstance(candidate, dict):
            top_parameter_view = candidate

    if top_parameter_view:
        weather = top_parameter_view.get("weather") if isinstance(top_parameter_view.get("weather"), dict) else {}
        source_contract = (
            top_parameter_view.get("source_contract")
            if isinstance(top_parameter_view.get("source_contract"), dict)
            else {}
        )
        decision = top_parameter_view.get("decision") if isinstance(top_parameter_view.get("decision"), dict) else {}
        with st.container(border=True):
            st.caption("Top Parameter Surface")
            cols_top = st.columns(4)
            with cols_top[0]:
                st.metric("Market", str(top_parameter_view.get("market_family") or "-"), help=str(top_parameter_view.get("market_question") or "-"))
                st.caption(str(top_parameter_view.get("market_id") or "-"))
            with cols_top[1]:
                st.metric("Weather", str(weather.get("forecast_value") or weather.get("observation_value") or "-"))
                st.caption(str(weather.get("station_id") or "-"))
            with cols_top[2]:
                st.metric("Source", str(source_contract.get("source_match_grade") or "-"))
                st.caption(str(source_contract.get("freshness_status") or "-"))
            with cols_top[3]:
                st.metric("Decision", str(decision.get("can_execute") or "-"))
                st.caption(str(decision.get("primary_block_reason") or "-"))

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
