from __future__ import annotations

import streamlit as st

from weather_dashboard.ui.compact_panel import render_panel_title, sanitize_text
from weather_dashboard.ui.field_dictionary import field_label


TOP_PARAMETER_RIBBON_VERSION = "top_parameter_ribbon.v1"


def build_top_parameter_ribbon_summary(
    *,
    market_snapshot: dict | None,
    forecast_snapshot: dict | None,
    resolver_rule: dict | None,
    probability_state: dict | None,
    comparison_row: dict | None,
    compact_gate_summary: dict | None,
    shanghai_live_weather: dict | None = None,
) -> dict:
    market = market_snapshot or {}
    forecast = forecast_snapshot or {}
    resolver = resolver_rule or {}
    probability = probability_state or {}
    comparison = comparison_row or {}
    gate = compact_gate_summary or {}
    live_weather = shanghai_live_weather or {}

    market_family = str(
        market.get("market_family")
        or resolver.get("market_family")
        or forecast.get("market_family")
        or comparison.get("market_family")
        or "-"
    )
    market_question = _first(
        market.get("market_question"),
        comparison.get("market_question"),
        forecast.get("market_question"),
        "-",
    )
    market_id = _first(market.get("market_id"), comparison.get("market_id"), forecast.get("market_id"), "-")
    location_name = _first(
        market.get("location_name"),
        resolver.get("location_name"),
        forecast.get("location_name"),
        "-",
    )
    target_date = _first(market.get("target_date"), forecast.get("target_date"), resolver.get("target_date"), "-")
    variable_name = _first(
        market.get("variable_name"),
        forecast.get("variable_name"),
        resolver.get("variable_name"),
        "-",
    )

    market_probability = _first(
        market.get("market_probability"),
        comparison.get("market_probability"),
        probability.get("market_probability"),
        "-",
    )
    yes_price = _first(market.get("yes_price"), "-")
    no_price = _first(market.get("no_price"), "-")
    favored_side = _first(market.get("favored_side"), "-")
    market_band = _first(market.get("market_band"), comparison.get("market_band"), "-")

    forecast_value = _first(forecast.get("value"), forecast.get("forecast_value"), "-")
    observation_value = _first(
        live_weather.get("observed_temp_c"),
        live_weather.get("observed_temp_max_24h_c"),
        live_weather.get("observed_temp_min_24h_c"),
        "-",
    )
    model_band = _first(forecast.get("model_band"), resolver.get("expected_band"), "-")
    unit = _infer_unit(market_family, resolver.get("unit") or forecast.get("unit"))
    station_name = _first(
        forecast.get("station_name"),
        live_weather.get("station_name"),
        resolver.get("station_name"),
        "-",
    )
    station_id = _first(
        forecast.get("station_id"),
        live_weather.get("station_code"),
        resolver.get("station_id"),
        "-",
    )
    timestamp = _first(
        live_weather.get("observed_valid_time"),
        forecast.get("timestamp"),
        forecast.get("forecast_target_date"),
        resolver.get("generated_at"),
        "-",
    )
    source_mode = _first(forecast.get("source_mode"), "-")
    required_data_source = _first(forecast.get("required_data_source"), resolver.get("required_data_source"), "-")

    settlement_source_type = _first(resolver.get("settlement_source_type"), "-")
    official_vs_proxy_source = _first(resolver.get("official_vs_proxy_source"), "-")
    source_match_grade = _first(resolver.get("source_match_grade"), "-")
    required_sources = ", ".join(str(item) for item in (resolver.get("required_sources") or []) if item) or "-"
    official_source_url = _first(resolver.get("official_source_url"), "-")
    freshness_status = _first(
        gate.get("validation_freshness_status"),
        gate.get("freshness_gate"),
        "-",
    )

    fair_value = _first(probability.get("fair_value"), comparison.get("fair_value"), "-")
    confidence_adjusted_edge = _first(
        probability.get("confidence_adjusted_edge"),
        probability.get("edge"),
        comparison.get("confidence_adjusted_gap"),
        "-",
    )
    comparison_status = _first(comparison.get("comparison_status"), "-")
    probability_mode = _first(probability.get("probability_mode"), gate.get("probability_mode"), "-")
    execution_constraint = _first(
        probability.get("execution_constraint"),
        gate.get("execution_constraint"),
        "-",
    )
    can_execute = "yes" if str(gate.get("gate_status") or "").upper() == "READY" else "no"
    blockers = [str(item) for item in (gate.get("blockers") or []) if item]
    primary_block_reason = blockers[0] if blockers else "none"
    recommended_action = _first(
        gate.get("recommended_operator_action"),
        comparison.get("action_hint"),
        "hold_execution_and_review",
    )

    cards = [
        {
            "title": "Market Identity",
            "metric_label": field_label("market_id"),
            "metric_value": market_id,
            "rows": [
                (field_label("market_question"), market_question),
                (field_label("market_family"), market_family),
                (field_label("location_name"), location_name),
                (field_label("target_date"), target_date),
                (field_label("variable_name"), variable_name),
            ],
        },
        {
            "title": "Polymarket Params",
            "metric_label": field_label("market_probability"),
            "metric_value": market_probability,
            "rows": [
                (field_label("yes_price"), yes_price),
                (field_label("no_price"), no_price),
                (field_label("favored_side"), favored_side),
                (field_label("market_band"), market_band),
            ],
        },
        {
            "title": "Weather Params",
            "metric_label": field_label("forecast_value") if forecast_value != "-" else field_label("observation_value"),
            "metric_value": forecast_value if forecast_value != "-" else observation_value,
            "rows": [
                (field_label("observation_value"), observation_value),
                (field_label("forecast_value"), forecast_value),
                (field_label("model_band"), model_band),
                (field_label("unit"), unit),
                (field_label("station_name"), station_name),
                (field_label("station_id"), station_id),
                (field_label("timestamp"), timestamp),
                (field_label("source_mode"), source_mode),
                (field_label("required_data_source"), required_data_source),
            ],
        },
        {
            "title": "Resolver / Source",
            "metric_label": field_label("source_match_grade"),
            "metric_value": source_match_grade,
            "rows": [
                (field_label("rule_status"), _first(resolver.get("resolver_status"), resolver.get("rule_status"), "-")),
                (field_label("settlement_source_type"), settlement_source_type),
                (field_label("official_vs_proxy_source"), official_vs_proxy_source),
                (field_label("required_sources"), required_sources),
                (field_label("freshness_status"), freshness_status),
                (field_label("official_source_url"), official_source_url),
            ],
        },
        {
            "title": "Comparison / Gate",
            "metric_label": field_label("can_execute"),
            "metric_value": can_execute,
            "rows": [
                (field_label("fair_value"), fair_value),
                (field_label("edge"), confidence_adjusted_edge),
                (field_label("comparison_status"), comparison_status),
                (field_label("primary_block_reason"), primary_block_reason),
                (field_label("execution_constraint"), execution_constraint),
                (field_label("recommended_operator_action"), recommended_action),
                (field_label("probability_mode"), probability_mode),
            ],
        },
    ]

    return {
        "schema_version": TOP_PARAMETER_RIBBON_VERSION,
        "market_id": market_id,
        "market_family": market_family,
        "market_question": market_question,
        "location_name": location_name,
        "target_date": target_date,
        "variable_name": variable_name,
        "cards": cards,
    }


def render_top_parameter_ribbon(summary: dict | None) -> None:
    if not summary:
        return

    render_panel_title(
        "Top Parameter Surface",
        "Market, weather, resolver and gate parameters are shown together as the first-screen operating context.",
    )
    cards = summary.get("cards") or []
    if not cards:
        return

    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            with st.container(border=True):
                st.caption(sanitize_text(card.get("title") or "-"))
                metric_value = card.get("metric_value")
                st.metric(
                    label=sanitize_text(card.get("metric_label") or "Value"),
                    value=sanitize_text(metric_value if metric_value not in (None, "") else "-"),
                )
                for label, value in card.get("rows") or []:
                    st.markdown(f"**{sanitize_text(label)}:** `{sanitize_text(value)}`")


def _infer_unit(market_family: str, explicit_unit: object | None) -> str:
    if explicit_unit not in (None, ""):
        return str(explicit_unit)
    family = str(market_family or "").lower()
    if "temperature" in family:
        return "celsius"
    if "precipitation" in family:
        return "mm"
    if "wind" in family:
        return "m/s"
    if "snow" in family:
        return "cm"
    if "sea_ice" in family:
        return "km²"
    return "-"


def _first(*values: object) -> object:
    for value in values:
        if value not in (None, ""):
            return value
    return "-"
