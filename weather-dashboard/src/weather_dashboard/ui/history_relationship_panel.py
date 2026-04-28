from __future__ import annotations

import pandas as pd
import streamlit as st


def build_history_relationship_summary(
    history_df: pd.DataFrame,
    selected_market_id: str | None,
) -> dict | None:
    if history_df.empty or not selected_market_id:
        return None

    working = history_df[history_df["market_id"] == selected_market_id].copy()
    if working.empty:
        return None

    working["timestamp"] = pd.to_datetime(working["timestamp"], errors="coerce")
    working = working.sort_values(by="timestamp")

    top_parameter_view = None
    if "top_parameter_view" in working.columns and not working.empty:
        candidate = working.iloc[-1].get("top_parameter_view")
        if isinstance(candidate, dict):
            top_parameter_view = candidate

    cols = [
        "timestamp",
        "market_probability",
        "confidence_adjusted_gap",
        "comparison_status",
        "model_band",
        "market_band",
    ]
    existing = [column for column in cols if column in working.columns]
    preview = working[existing].copy()

    numeric_cols = [
        column for column in ["market_probability", "confidence_adjusted_gap"] if column in working.columns
    ]
    chart_df = working[["timestamp", *numeric_cols]].set_index("timestamp") if numeric_cols else None

    return {
        "working": working,
        "preview": preview,
        "top_parameter_view": top_parameter_view,
        "numeric_cols": numeric_cols,
        "chart_df": chart_df,
    }


def render_history_relationship_panel(
    history_df: pd.DataFrame,
    selected_market_id: str | None,
    *,
    summary: dict | None = None,
) -> None:
    st.subheader("History / Odds Relationship")

    summary = summary or build_history_relationship_summary(history_df, selected_market_id)

    if summary is None:
        if history_df.empty:
            st.info("No comparison history available.")
        elif not selected_market_id:
            st.info("Select a market to inspect history relationship.")
        else:
            st.info("No historical rows for selected market.")
        return

    working = summary["working"]
    preview = summary["preview"]
    top_parameter_view = summary["top_parameter_view"]
    numeric_cols = summary["numeric_cols"]
    chart_df = summary["chart_df"]

    if top_parameter_view:
        with st.container(border=True):
            st.caption("Top Parameter Surface")
            market = top_parameter_view.get("market_id", "-")
            market_family = top_parameter_view.get("market_family", "-")
            weather = top_parameter_view.get("weather") if isinstance(top_parameter_view.get("weather"), dict) else {}
            source_contract = (
                top_parameter_view.get("source_contract")
                if isinstance(top_parameter_view.get("source_contract"), dict)
                else {}
            )
            decision = top_parameter_view.get("decision") if isinstance(top_parameter_view.get("decision"), dict) else {}
            cols_top = st.columns(4)
            with cols_top[0]:
                st.metric("Market", f"{market_family}", help=str(top_parameter_view.get("market_question") or "-"))
                st.caption(f"{market}")
            with cols_top[1]:
                st.metric("Weather", str(weather.get("forecast_value") or weather.get("observation_value") or "-"))
                st.caption(f"{weather.get('station_id', '-')}")
            with cols_top[2]:
                st.metric("Source", str(source_contract.get("source_match_grade") or "-"))
                st.caption(str(source_contract.get("freshness_status") or "-"))
            with cols_top[3]:
                st.metric("Decision", str(decision.get("can_execute") or "-"))
                st.caption(str(decision.get("primary_block_reason") or "-"))

    if numeric_cols:
        chart_df = chart_df if chart_df is not None else working[["timestamp", *numeric_cols]].set_index("timestamp")
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
