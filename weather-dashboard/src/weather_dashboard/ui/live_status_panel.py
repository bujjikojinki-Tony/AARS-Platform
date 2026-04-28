from __future__ import annotations

import streamlit as st

from weather_dashboard.ui.compact_panel import (
    render_compact_note,
    render_kv_section,
    render_panel_title,
    sanitize_text,
    semantic_tone,
    semantic_value_html,
)
from weather_dashboard.ui.field_dictionary import field_label
from weather_dashboard.ui.operator_messages import (
    NO_REALTIME_FORECAST_SNAPSHOT,
    NO_REALTIME_MARKET_SNAPSHOT,
)


def render_live_status_panel(
    market_snapshot: dict | None,
    forecast_snapshot: dict | None,
    *,
    key_prefix: str = "live_status",
) -> None:
    render_panel_title("Live Status")

    selected_market_id = str(market_snapshot.get("market_id") or "") if market_snapshot else ""
    forecast_market_id = str(forecast_snapshot.get("market_id") or "") if forecast_snapshot else ""
    forecast_matches_market = bool(
        selected_market_id and forecast_market_id and selected_market_id == forecast_market_id
    )

    if not market_snapshot:
        st.info(NO_REALTIME_MARKET_SNAPSHOT)
    if not forecast_snapshot:
        st.info(NO_REALTIME_FORECAST_SNAPSHOT)
    if not market_snapshot and not forecast_snapshot:
        return

    if selected_market_id and forecast_market_id and not forecast_matches_market:
        render_compact_note(
            "Forecast / resolver snapshot is for a different market than the selected Polymarket snapshot.",
            tone="warning",
        )

    cards: list[dict] = []
    if market_snapshot:
        cards.append(
                {
                    "title": "POLYMARKET",
                    "status": market_snapshot.get("market_probability", "-"),
                    "rows": [
                        ("Market ID", market_snapshot.get("market_id", "-")),
                    ("Favored Side", market_snapshot.get("favored_side", "-")),
                    ("YES / NO", f"{market_snapshot.get('yes_price', '-')} / {market_snapshot.get('no_price', '-')}"),
                    (field_label("generated_at"), market_snapshot.get("updated_at", "-")),
                ],
            }
        )

    resolution_snapshot = {}
    if forecast_snapshot:
        resolution_snapshot = forecast_snapshot.get("resolution_snapshot") or {}
        cards.append(
            {
                "title": "FORECAST",
                "status": forecast_snapshot.get("value", "-"),
                "rows": [
                    ("Market ID", forecast_snapshot.get("market_id", "-")),
                    (field_label("rule_status"), forecast_snapshot.get("rule_status", "-")),
                    (field_label("model_band"), forecast_snapshot.get("model_band", "-")),
                    (field_label("target_date"), forecast_snapshot.get("target_date", "-")),
                ],
            }
        )
        if resolution_snapshot:
            cards.append(
                {
                    "title": "RESOLVER",
                    "status": resolution_snapshot.get("comparison_hint", "-"),
                    "rows": [
                        ("Family", forecast_snapshot.get("market_family", "-")),
                        ("Source", forecast_snapshot.get("required_data_source", "-")),
                        (field_label("expected_band"), resolution_snapshot.get("expected_band", "-")),
                        ("Scope", forecast_snapshot.get("resolution_scope", "-")),
                    ],
                }
            )

    cols = st.columns(min(len(cards), 3))
    for col, card in zip(cols, cards):
        with col:
            with st.container(border=True):
                st.caption(sanitize_text(card["title"]))
                status_tone = semantic_tone("status", card["status"])
                st.markdown(
                    f"""
                    <div class="compact-metric compact-metric--{status_tone}">
                      <span>Status</span>
                      <strong>{semantic_value_html("Status", card["status"], metric=True)}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                for label, value in card["rows"]:
                    st.markdown(
                        f"<div class='compact-kv-row compact-kv-row--{semantic_tone(label, value)}'>"
                        f"<span>{sanitize_text(label)}</span>"
                        f"<strong>{semantic_value_html(label, value)}</strong>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

    if st.checkbox(
        "Show live status details",
        value=False,
        key=f"{key_prefix}_show_details",
    ):
        detail_col1, detail_col2 = st.columns(2)
        with detail_col1:
            if market_snapshot:
                render_kv_section(
                    "Polymarket Snapshot",
                    [
                        ("Market ID", market_snapshot.get("market_id", "-")),
                        ("Question", market_snapshot.get("market_question", "-")),
                        ("Location", market_snapshot.get("location_name", "-")),
                        ("Updated At", market_snapshot.get("updated_at", "-")),
                        ("Favored Side", market_snapshot.get("favored_side", "-")),
                        ("Yes Price", market_snapshot.get("yes_price", "-")),
                        ("No Price", market_snapshot.get("no_price", "-")),
                        ("Market Band Scheme", market_snapshot.get("market_band_scheme", "-")),
                        ("Market Band", market_snapshot.get("market_band", "-")),
                    ],
                    metric_label="Market Probability",
                    metric_value=market_snapshot.get("market_probability", "-"),
                )
        with detail_col2:
            if forecast_snapshot:
                forecast_items = [
                    ("Market ID", forecast_snapshot.get("market_id", "-")),
                    ("Market Family", forecast_snapshot.get("market_family", "-")),
                    ("Rule Status", forecast_snapshot.get("rule_status", "-")),
                    ("Resolution Scope", forecast_snapshot.get("resolution_scope", "-")),
                    ("Required Data Source", forecast_snapshot.get("required_data_source", "-")),
                    ("Expected Band", resolution_snapshot.get("expected_band", "-")),
                    ("Comparison Hint", resolution_snapshot.get("comparison_hint", "-")),
                    ("Location", forecast_snapshot.get("location_name", "-")),
                    ("Target Date", forecast_snapshot.get("target_date", "-")),
                    ("Variable", forecast_snapshot.get("variable_name", "-")),
                    ("Timestamp", forecast_snapshot.get("timestamp", "-")),
                    ("Model Band", forecast_snapshot.get("model_band", "-")),
                    ("Confidence Score", forecast_snapshot.get("confidence_score", "-")),
                    ("Forecast Status", forecast_snapshot.get("source_mode", "-")),
                    ("Notes", forecast_snapshot.get("notes", "-")),
                ]
                if selected_market_id and not forecast_matches_market:
                    forecast_items.insert(0, ("Selected Polymarket ID", selected_market_id))
                    forecast_items.insert(1, ("Resolver Market ID", forecast_market_id or "-"))
                render_kv_section(
                    "Forecast / Resolver Snapshot",
                    forecast_items,
                    metric_label="Value",
                    metric_value=forecast_snapshot.get("value", "-"),
                )
        if resolution_snapshot:
            st.json({"structured_resolution": resolution_snapshot})
        if forecast_snapshot and selected_market_id and not forecast_matches_market:
            st.json({"different_market_resolver_snapshot": forecast_snapshot})

    if forecast_snapshot and forecast_snapshot.get("rule_status") not in (
        None,
        "matched",
        "matched_index",
        "matched_snapshot",
    ):
        render_compact_note(
            "The current live market does not have a matching weather rule yet.",
            tone="warning",
        )
