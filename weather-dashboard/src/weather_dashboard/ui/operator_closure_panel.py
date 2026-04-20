from __future__ import annotations

import pandas as pd
import streamlit as st

from weather_dashboard.ui.compact_panel import render_panel_title, sanitize_text


def _latest_row(df: pd.DataFrame | None) -> dict:
    if df is None or df.empty:
        return {}
    return df.iloc[0].to_dict()


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    try:
        if isinstance(value, float):
            return f"{value:.2f}"
    except Exception:
        pass
    return str(value)


def _fmt_prob(value: object) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value)


def render_operator_closure_panel(
    comparison_df: pd.DataFrame | None,
    market_snapshot: dict | None,
    forecast_snapshot: dict | None,
    bot_authorized: bool,
) -> None:
    row = _latest_row(comparison_df)

    market_id = (market_snapshot or {}).get("market_id") or row.get("market_id") or "-"
    market_question = (market_snapshot or {}).get("market_question") or row.get("market_question") or "No market selected"
    market_family = (market_snapshot or {}).get("market_family") or row.get("market_family") or "-"

    yes_price = (market_snapshot or {}).get("yes_price") or row.get("yes_price")
    no_price = (market_snapshot or {}).get("no_price") or row.get("no_price")
    market_probability = (market_snapshot or {}).get("market_probability") if market_snapshot else row.get("market_probability")
    favored_side = (market_snapshot or {}).get("favored_side") or row.get("favored_side") or "-"

    model_value = (forecast_snapshot or {}).get("value") or row.get("model_value")
    model_band = (forecast_snapshot or {}).get("model_band") or row.get("model_band") or "-"
    rule_status = (forecast_snapshot or {}).get("rule_status") or row.get("rule_status") or "-"
    required_data_source = (forecast_snapshot or {}).get("required_data_source") or row.get("required_data_source") or "-"
    confidence_score = (forecast_snapshot or {}).get("confidence_score") or row.get("confidence_score")

    comparison_status = row.get("comparison_status") or "-"
    gap = row.get("confidence_adjusted_gap")
    band_distance = row.get("band_distance")

    resolver_market_id = (forecast_snapshot or {}).get("market_id")
    forecast_matches_market = bool(
        resolver_market_id and market_id != "-" and str(resolver_market_id) == str(market_id)
    )
    blocked_statuses = {"market_mismatch", "unmatched_rule", "-", None}
    action_side = "YES" if str(favored_side).lower() == "yes" else "NO"
    can_bot_act = bool(
        bot_authorized
        and comparison_status not in blocked_statuses
        and forecast_matches_market
    )

    render_panel_title("Operator Decision Closure")

    cards = [
        (
            "Market Context",
            market_question,
            f"market_id={market_id} · family={market_family}",
        ),
        (
            "Price Context",
            f"favored={favored_side} · prob={_fmt_prob(market_probability)}",
            f"YES={_fmt_prob(yes_price)} · NO={_fmt_prob(no_price)}",
        ),
        (
            "Resolver Evidence",
            f"value={_fmt(model_value)} · band={model_band}",
            f"rule={rule_status} · confidence={_fmt_prob(confidence_score)} · source={required_data_source}",
        ),
        (
            "Comparison",
            str(comparison_status),
            f"gap={_fmt_prob(gap)} · band_distance={_fmt(band_distance)}",
        ),
        (
            "BOT Action",
            "CAN ACT" if can_bot_act else "LOCKED / WAIT",
            f"authorized={bot_authorized} · action={action_side} · resolver_match={forecast_matches_market}",
        ),
    ]

    cols = st.columns(2)
    for idx, card in enumerate(cards):
        with cols[idx % 2]:
            with st.container(border=True):
                st.caption(card[0].upper())
                st.metric("Status", sanitize_text(card[1]))
                st.caption(sanitize_text(card[2]))
