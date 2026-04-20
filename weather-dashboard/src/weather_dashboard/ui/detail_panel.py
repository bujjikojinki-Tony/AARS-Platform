import streamlit as st
import pandas as pd

from weather_dashboard.models.market_detail_state import MarketDetailState


def build_detail_state(df: pd.DataFrame, market_id: str) -> MarketDetailState | None:
    filtered = df[df["market_id"] == market_id]
    if filtered.empty:
        return None

    row = filtered.iloc[0].to_dict()

    return MarketDetailState(
        market_id=row.get("market_id"),
        market_question=row.get("market_question"),
        location_name=row.get("location_name"),
        target_date=row.get("target_date"),
        variable_name=row.get("variable_name"),
        model_band=row.get("model_band"),
        market_band=row.get("market_band"),
        confidence_score=row.get("confidence_score"),
        confidence_adjusted_gap=row.get("confidence_adjusted_gap"),
        comparison_status=row.get("comparison_status"),
        action_hint=row.get("action_hint"),
    )


def render_detail_panel(df: pd.DataFrame, selected_market_id: str | None) -> None:
    st.subheader("Market Detail")

    if df.empty:
        st.info("No rows available.")
        return

    if not selected_market_id:
        st.info("Select a market to view detail.")
        return

    detail = build_detail_state(df, selected_market_id)
    if detail is None:
        st.info("No detail found for selected market.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Market ID:** `{detail.market_id}`")
        st.markdown(f"**Question:** {detail.market_question}")
        st.markdown(f"**Location:** {detail.location_name}")
        st.markdown(f"**Target Date:** {detail.target_date}")
        st.markdown(f"**Variable:** {detail.variable_name}")

    with col2:
        st.markdown(f"**Model Band:** {detail.model_band}")
        st.markdown(f"**Market Band:** {detail.market_band}")
        st.markdown(f"**Confidence Score:** {detail.confidence_score}")
        st.markdown(f"**Adjusted Gap:** {detail.confidence_adjusted_gap}")
        st.markdown(f"**Status:** {detail.comparison_status}")
        st.markdown(f"**Action Hint:** {detail.action_hint}")
