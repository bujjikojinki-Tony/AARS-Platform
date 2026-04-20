from __future__ import annotations

import pandas as pd
import streamlit as st

from weather_dashboard.ui.compact_panel import (
    render_compact_note,
    render_kv_section,
    render_panel_title,
)


def _latest_row(df: pd.DataFrame) -> dict | None:
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def render_comparison_focus_panel(
    comparison_df: pd.DataFrame,
    market_snapshot: dict | None,
    forecast_snapshot: dict | None,
) -> None:
    row = _latest_row(comparison_df) if comparison_df is not None else None

    if row is None and not market_snapshot and not forecast_snapshot:
        st.info("No comparison snapshot available.")
        return

    market_question = row.get("market_question") if row else None
    market_id = row.get("market_id") if row else None
    forecast_market_id = row.get("forecast_market_id") if row else None
    rule_status = row.get("rule_status") if row else None
    rule_market_id = row.get("rule_market_id") if row else None
    comparison_status = row.get("comparison_status") if row else None
    confidence_adjusted_gap = row.get("confidence_adjusted_gap") if row else None
    band_distance = row.get("band_distance") if row else None
    band_scheme = row.get("band_scheme") if row else None
    market_band_scheme = row.get("market_band_scheme") if row else None
    favored_side = row.get("favored_side") if row else None
    market_probability = row.get("market_probability") if row else None
    yes_price = row.get("yes_price") if row else None
    no_price = row.get("no_price") if row else None
    model_value = row.get("model_value") if row else None
    model_band = row.get("model_band") if row else None
    target_date = row.get("target_date") if row else None
    variable_name = row.get("variable_name") if row else None
    market_family = row.get("market_family") if row else None
    resolution_scope = row.get("resolution_scope") if row else None
    supported_by_current_pipeline = row.get("supported_by_current_pipeline") if row else None
    required_data_source = row.get("required_data_source") if row else None
    market_question_display = (
        market_question
        or (market_snapshot.get("market_question") if market_snapshot else "-")
    )
    favored_side_display = favored_side or (market_snapshot.get("favored_side") if market_snapshot else "-")
    yes_price_display = yes_price if yes_price is not None else (
        market_snapshot.get("yes_price") if market_snapshot else "-"
    )
    no_price_display = no_price if no_price is not None else (
        market_snapshot.get("no_price") if market_snapshot else "-"
    )
    model_band_display = model_band or (
        forecast_snapshot.get("model_band") if forecast_snapshot else "-"
    )
    target_date_display = target_date or (
        forecast_snapshot.get("target_date") if forecast_snapshot else "-"
    )
    variable_name_display = variable_name or (
        forecast_snapshot.get("variable_name") if forecast_snapshot else "-"
    )
    source_market_id = market_id or (market_snapshot.get("market_id") if market_snapshot else "-")
    latest_market_ref = row.get("market_snapshot_ref", "-") if row else "-"
    latest_forecast_ref = row.get("forecast_snapshot_ref", "-") if row else "-"
    comparison_reason = row.get("comparison_reason") if row else None
    market_probability_display = (
        f"{float(market_probability):.2f}" if market_probability is not None else "-"
    )
    model_value_display = f"{float(model_value):.1f}" if model_value is not None else "-"
    gap_display = (
        f"{float(confidence_adjusted_gap):.2f}"
        if confidence_adjusted_gap is not None
        else "-"
    )

    render_panel_title("Comparison Focus", f"Market: {market_question_display}")

    if comparison_status == "unmatched_rule":
        render_compact_note(
            "The live market was loaded, but no weather rule matched it yet. "
            "This is a real market-aware state, not a broken comparison.",
            tone="warning",
        )
        if comparison_reason:
            st.caption(comparison_reason)
    elif comparison_status == "market_mismatch":
        render_compact_note(
            "The current forecast snapshot belongs to a different market. "
            "We are showing the live Polymarket market, but the forecast poller "
            "is still producing a snapshot for another market_id.",
            tone="warning",
        )
        if comparison_reason:
            st.caption(comparison_reason)
    elif comparison_status in (None, "unknown") or model_band in (None, "-"):
        render_compact_note(
            "This market is live on Polymarket, but the weather forecast side has not "
            "matched cleanly yet. That usually means the current forecast extractor is "
            "tracking a different rule or has no usable value for this market.",
            tone="warning",
        )

    left, mid, right = st.columns(3)

    with left:
        render_kv_section(
            "Polymarket",
            [
                ("Favored Side", favored_side_display),
                ("Yes Price", yes_price_display),
                ("No Price", no_price_display),
            ],
            metric_label="Market Probability",
            metric_value=market_probability_display,
        )

    with mid:
        render_kv_section(
            "Forecast",
            [
                ("Model Band", model_band_display),
                ("Target Date", target_date_display),
                ("Variable", variable_name_display),
                ("Market Family", market_family or "-"),
                ("Resolution Scope", resolution_scope or "-"),
                (
                    "Pipeline Supported",
                    supported_by_current_pipeline if supported_by_current_pipeline is not None else "-",
                ),
                ("Required Data Source", required_data_source or "-"),
            ],
            metric_label="Model Value",
            metric_value=model_value_display,
        )

    with right:
        comparison_items = [
            ("Status", comparison_status or "-"),
            ("Band Distance", band_distance if band_distance is not None else "-"),
            ("Rule Status", rule_status or "-"),
            ("Rule Market ID", rule_market_id or "-"),
            ("Band Scheme", band_scheme or "-"),
            ("Market Band Scheme", market_band_scheme or "-"),
        ]
        if forecast_market_id:
            comparison_items.append(("Forecast Market ID", forecast_market_id))
        render_kv_section(
            "Comparison",
            comparison_items,
            metric_label="Gap",
            metric_value=gap_display,
        )
        if row:
            st.caption(
                f"Latest row: {source_market_id} | "
                f"market ref {latest_market_ref} | "
                f"forecast ref {latest_forecast_ref}"
            )
