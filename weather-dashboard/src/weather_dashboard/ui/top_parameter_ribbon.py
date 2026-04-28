from __future__ import annotations

import re

from weather_dashboard.ui.compact_panel import (
    render_panel_title,
    render_stat_strip,
    sanitize_text,
    semantic_tone,
)
from weather_dashboard.ui.field_dictionary import field_label
from weather_dashboard.ui.top_parameter_family_profiles import get_family_top_parameter_profile
from weather_dashboard.ui.top_parameter_view import TOP_PARAMETER_VIEW_VERSION, TopParameterView


def build_top_parameter_ribbon_summary(
    *,
    market_snapshot: dict | None,
    forecast_snapshot: dict | None,
    resolver_rule: dict | None,
    probability_state: dict | None,
    comparison_row: dict | None,
    compact_gate_summary: dict | None,
    validation_freshness_status: dict | None = None,
    observation_snapshot: dict | None = None,
    shanghai_live_weather: dict | None = None,
) -> TopParameterView:
    market = market_snapshot or {}
    forecast = forecast_snapshot or {}
    resolver = resolver_rule or {}
    probability = probability_state or {}
    comparison = comparison_row or {}
    gate = compact_gate_summary or {}
    live_weather = observation_snapshot or shanghai_live_weather or {}

    market_family = str(
        market.get("market_family")
        or resolver.get("market_family")
        or forecast.get("market_family")
        or comparison.get("market_family")
        or "-"
    )
    family_profile = get_family_top_parameter_profile(market_family)
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
    target_date = _first(
        _normalize_market_question_target_date(market_question),
        market.get("target_date"),
        forecast.get("target_date"),
        resolver.get("target_date"),
        "-",
    )
    variable_name = _first(
        market.get("variable_name"),
        forecast.get("variable_name"),
        resolver.get("variable_name"),
        "-",
    )

    market_probability = _first(
        _derive_market_probability(market),
        _derive_market_probability(comparison),
        probability.get("market_probability"),
        "unavailable",
    )
    yes_price = _first(market.get("yes_price"), "-")
    no_price = _first(market.get("no_price"), "-")
    favored_side = _first(market.get("favored_side"), "-")
    market_band = _first(market.get("market_band"), comparison.get("market_band"), "-")

    forecast_display_value = _first(
        forecast.get("display_value"),
        forecast.get("forecast_display_value"),
        forecast.get("forecast_value"),
        forecast.get("value"),
        "-",
    )
    forecast_value = forecast_display_value
    observation_display_value = _first(
        live_weather.get("display_value"),
        live_weather.get("observation_display_value"),
        live_weather.get("observation_value"),
        live_weather.get("official_value"),
        live_weather.get("observed_temp_c"),
        live_weather.get("observed_temp_max_24h_c"),
        live_weather.get("observed_temp_min_24h_c"),
        "-",
    )
    observation_value = observation_display_value
    forecast_raw_value = _first(forecast.get("raw_value"), forecast.get("forecast_raw_value"), "-")
    forecast_canonical_value = _first(
        forecast.get("canonical_value"),
        forecast.get("forecast_canonical_value"),
        "-",
    )
    observation_raw_value = _first(
        live_weather.get("raw_value"),
        live_weather.get("observation_raw_value"),
        "-",
    )
    observation_canonical_value = _first(
        live_weather.get("canonical_value"),
        live_weather.get("observation_canonical_value"),
        "-",
    )
    observation_band = _first(
        live_weather.get("observation_band"),
        live_weather.get("official_band"),
        "-",
    )
    model_band = _first(forecast.get("model_band"), resolver.get("expected_band"), "-")
    unit = _first(
        resolver.get("unit"),
        forecast.get("unit"),
        live_weather.get("unit"),
        family_profile.get("unit"),
        _infer_unit(market_family, None),
    )
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
    observed_at = _first(
        live_weather.get("observed_at"),
        live_weather.get("observed_valid_time"),
        forecast.get("timestamp"),
        resolver.get("generated_at"),
        "-",
    )
    forecast_timestamp = _first(
        forecast.get("forecast_timestamp"),
        forecast.get("timestamp"),
        "-",
    )
    source_mode = _first(forecast.get("source_mode"), "-")
    required_data_source = _first(forecast.get("required_data_source"), resolver.get("required_data_source"), "-")
    canonical_unit = _first(
        forecast.get("canonical_unit"),
        resolver.get("canonical_unit"),
        unit,
    )
    source_priority = _first(
        resolver.get("source_priority"),
        forecast.get("source_priority"),
        market.get("source_priority"),
        "-",
    )
    fallback_mode = _first(
        forecast.get("source_mode"),
        resolver.get("fallback_mode"),
        resolver.get("fallback_policy"),
        "-",
    )
    precision_policy_ref = _first(
        resolver.get("precision_policy_ref"),
        forecast.get("precision_policy_ref"),
        market.get("precision_policy_ref"),
        "-",
    )
    rounding_policy_ref = _first(
        resolver.get("rounding_policy_ref"),
        forecast.get("rounding_policy_ref"),
        market.get("rounding_policy_ref"),
        "-",
    )
    band_mapping_policy_ref = _first(
        resolver.get("band_mapping_policy_ref"),
        forecast.get("band_mapping_policy_ref"),
        market.get("band_mapping_policy_ref"),
        "-",
    )
    source_policy_ref = _first(
        resolver.get("source_policy_ref"),
        forecast.get("source_policy_ref"),
        market.get("source_policy_ref"),
        "-",
    )

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
    freshness_reason = _build_freshness_reason(
        validation_freshness_status=validation_freshness_status,
        gate=gate,
    )
    freshness_age = _build_freshness_age(validation_freshness_status)
    realtime_compare_value = _build_realtime_compare_value(
        observation_display_value=observation_display_value,
        forecast_display_value=forecast_display_value,
        observation_canonical_value=observation_canonical_value,
        forecast_canonical_value=forecast_canonical_value,
        unit=unit,
    )
    forecast_reason = _build_forecast_reason(
        forecast=forecast,
        resolver=resolver,
        comparison=comparison,
        gate=gate,
        live_weather=live_weather,
    )
    weather_metric_label = "Live Temp vs Forecast"
    weather_metric_value = (
        realtime_compare_value
        if forecast_value not in ("-", "unavailable") and observation_value not in ("-", "unavailable")
        else (forecast_value if forecast_value != "-" else "unavailable")
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
    top_parameter_view = {
        "schema_version": TOP_PARAMETER_VIEW_VERSION,
        "market_id": market_id,
        "market_family": market_family,
        "market_question": market_question,
        "location_name": location_name,
        "target_date": target_date,
        "variable_name": variable_name,
        "polymarket": {
            "yes_price": yes_price,
            "no_price": no_price,
            "market_implied_probability": market_probability,
            "favored_side": favored_side,
            "market_band": market_band,
        },
        "weather": {
            "observation_value": observation_value,
            "observation_display_value": observation_display_value,
            "observation_raw_value": observation_raw_value,
            "observation_canonical_value": observation_canonical_value,
            "observation_band": _first(live_weather.get("observation_band"), live_weather.get("official_band"), "-"),
            "forecast_value": forecast_value,
            "forecast_display_value": forecast_display_value,
            "forecast_raw_value": forecast_raw_value,
            "forecast_canonical_value": forecast_canonical_value,
            "unit": unit,
            "canonical_unit": canonical_unit,
            "model_band": model_band,
            "official_band": _first(resolver.get("official_band"), "-"),
            "station_name": station_name,
            "station_id": station_id,
            "observed_at": _first(live_weather.get("observed_at"), live_weather.get("observed_valid_time"), "-"),
            "forecast_timestamp": _first(forecast.get("forecast_timestamp"), forecast.get("timestamp"), "-"),
            "settlement_ready": _first(live_weather.get("settlement_ready"), "-"),
        },
        "source_contract": {
            "settlement_source_type": settlement_source_type,
            "official_vs_proxy_source": official_vs_proxy_source,
            "source_match_grade": source_match_grade,
            "required_sources": required_sources,
            "official_source_url": official_source_url,
            "freshness_status": freshness_status,
            "source_priority": source_priority,
            "fallback_mode": fallback_mode,
            "source_policy_ref": source_policy_ref,
            "precision_policy_ref": precision_policy_ref,
            "rounding_policy_ref": rounding_policy_ref,
            "band_mapping_policy_ref": band_mapping_policy_ref,
        },
        "decision": {
            "fair_value": fair_value,
            "edge": confidence_adjusted_edge,
            "probability_mode": probability_mode,
            "execution_constraint": execution_constraint,
            "can_execute": can_execute,
            "primary_block_reason": primary_block_reason,
            "recommended_operator_action": recommended_action,
            "comparison_status": comparison_status,
        },
    }

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
            "title": "Weather / Forecast Params",
            "metric_label": weather_metric_label,
            "metric_value": weather_metric_value,
            "rows": [
                (family_profile.get("observation_label", field_label("observation_value")), observation_value),
                (family_profile.get("forecast_label", field_label("forecast_value")), forecast_value),
                ("Realtime Compare", realtime_compare_value),
                ("Forecast Reason", forecast_reason),
                ("Freshness Reason", freshness_reason),
                ("Observation Raw", observation_raw_value),
                ("Observation Canonical", observation_canonical_value),
                ("Forecast Raw", forecast_raw_value),
                ("Forecast Canonical", forecast_canonical_value),
                (field_label("model_band"), model_band),
                (field_label("unit"), unit),
                ("Canonical Unit", canonical_unit),
                (field_label("station_name"), station_name),
                (field_label("station_id"), station_id),
                (field_label("observed_at"), observed_at),
                (field_label("forecast_timestamp"), forecast_timestamp),
                (field_label("source_mode"), source_mode),
                (field_label("required_data_source"), required_data_source),
                (field_label("settlement_ready"), live_weather.get("settlement_ready", "-")),
            ],
        },
        {
            "title": "Resolver / Source Contract",
            "metric_label": field_label("source_match_grade"),
            "metric_value": source_match_grade,
            "rows": [
                (field_label("rule_status"), _first(resolver.get("resolver_status"), resolver.get("rule_status"), "-")),
                (field_label("settlement_source_type"), settlement_source_type),
                (field_label("official_vs_proxy_source"), official_vs_proxy_source),
                (field_label("required_sources"), required_sources),
                (field_label("freshness_status"), freshness_status),
                ("Freshness Age", freshness_age),
                ("Freshness Reason", freshness_reason),
                (field_label("official_source_url"), official_source_url),
                ("Source Priority", source_priority),
                ("Fallback Mode", fallback_mode),
                ("Source Policy Ref", source_policy_ref),
                ("Precision Policy Ref", precision_policy_ref),
                ("Rounding Policy Ref", rounding_policy_ref),
                ("Band Mapping Policy Ref", band_mapping_policy_ref),
            ],
        },
        {
            "title": "Comparison / Gate Summary",
            "metric_label": field_label("can_execute"),
            "metric_value": can_execute,
            "rows": [
                (field_label("fair_value"), fair_value),
                (field_label("edge"), confidence_adjusted_edge),
                (field_label("comparison_status"), comparison_status),
                (field_label("freshness_status"), freshness_status),
                ("Freshness Age", freshness_age),
                ("Freshness Reason", freshness_reason),
                (field_label("primary_block_reason"), primary_block_reason),
                (field_label("execution_constraint"), execution_constraint),
                (field_label("recommended_operator_action"), recommended_action),
                (field_label("probability_mode"), probability_mode),
            ],
        },
    ]

    return {
        **top_parameter_view,
        "cards": cards,
    }


def render_top_parameter_ribbon(summary: TopParameterView | None) -> None:
    import streamlit as st

    if not summary:
        return

    cards = summary.get("cards") or []
    if not cards:
        return

    render_panel_title(
        "Top Parameter Surface",
        "Compact first-screen context. Open details only when you need the full resolver / weather / gate surface.",
    )
    render_stat_strip(_build_top_parameter_compact_items(summary), title="First-screen summary")

    with st.expander("Open full parameter surface", expanded=False):
        max_cols = 4
        for row_start in range(0, len(cards), max_cols):
            row_cards = cards[row_start : row_start + max_cols]
            cols = st.columns(len(row_cards))
            for col, card in zip(cols, row_cards):
                rendered_rows = [
                    (label, value)
                    for label, value in (card.get("rows") or [])
                    if not _is_empty_value(value)
                ]
                metric_value = card.get("metric_value")
                has_metric = not _is_empty_value(metric_value)
                if not rendered_rows and not has_metric:
                    continue
                with col:
                    with st.container(border=True):
                        st.markdown(
                            f"""
                            <div style="
                                color:#f7fbff;
                                font-family:'Avenir Next Condensed','DIN Condensed','Trebuchet MS',sans-serif;
                                font-size:0.92rem;
                                font-weight:950;
                                letter-spacing:0.04em;
                                line-height:1.06;
                                margin-bottom:0.14rem;
                            ">{sanitize_text(card.get('title') or '-')}</div>
                            """,
                            unsafe_allow_html=True,
                        )
                        metric_label = sanitize_text(card.get("metric_label") or "Value")
                        metric_tone = semantic_tone(metric_label, metric_value)
                        st.markdown(
                            f"""
                            <div style="
                                border:1px solid rgba(255, 255, 255, 0.12);
                                border-radius:10px;
                                background:rgba(12, 15, 20, 0.98);
                                padding:0.28rem 0.34rem 0.26rem;
                                margin-top:0.12rem;
                            ">
                              <div style="color:#a3adb7;font-size:0.54rem;font-weight:850;letter-spacing:0.12em;text-transform:uppercase;">
                                {metric_label}
                              </div>
                              <div style="
                                color:{_tone_color(metric_tone)};
                                font-size:1rem;
                                font-weight:900;
                                line-height:1.10;
                                margin-top:0.08rem;
                                font-variant-numeric:tabular-nums;
                              ">
                                {sanitize_text(metric_value)}
                              </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        rows_html = "\n".join(
                            _render_top_parameter_row(label, value) for label, value in rendered_rows
                        )
                        st.markdown(rows_html, unsafe_allow_html=True)


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


def _normalize_market_question_target_date(question: object | None) -> str | None:
    text = str(question or "").strip()
    if not text:
        return None
    match = re.search(
        r"\b(?P<month>jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
        r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sept?(?:ember)?|oct(?:ober)?|"
        r"nov(?:ember)?|dec(?:ember)?)\.?\s+(?P<day>\d{1,2})(?:,\s*(?P<year>\d{4}))?\b",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    month_key = match.group("month").lower().rstrip(".")
    month_map = {
        "jan": "Jan",
        "january": "Jan",
        "feb": "Feb",
        "february": "Feb",
        "mar": "Mar",
        "march": "Mar",
        "apr": "Apr",
        "april": "Apr",
        "may": "May",
        "jun": "Jun",
        "june": "Jun",
        "jul": "Jul",
        "july": "Jul",
        "aug": "Aug",
        "august": "Aug",
        "sep": "Sep",
        "sept": "Sep",
        "september": "Sep",
        "oct": "Oct",
        "october": "Oct",
        "nov": "Nov",
        "november": "Nov",
        "dec": "Dec",
        "december": "Dec",
    }
    month = month_map.get(month_key)
    if not month:
        return None
    return f"{month} {int(match.group('day'))}"


def _first(*values: object) -> object:
    for value in values:
        if value not in (None, ""):
            return value
    return "-"


def _build_realtime_compare_value(
    *,
    observation_display_value: object,
    forecast_display_value: object,
    observation_canonical_value: object,
    forecast_canonical_value: object,
    unit: object,
) -> str:
    obs_numeric = _as_float(observation_canonical_value)
    fcst_numeric = _as_float(forecast_canonical_value)
    display_unit = str(unit or "").strip()
    unit_suffix = f" {display_unit}" if display_unit and display_unit != "-" else ""
    if obs_numeric is not None and fcst_numeric is not None:
        delta = obs_numeric - fcst_numeric
        return (
            f"Obs { _format_numeric(obs_numeric) }{unit_suffix} vs "
            f"Fcst { _format_numeric(fcst_numeric) }{unit_suffix} "
            f"(Δ {_format_signed_numeric(delta)}{unit_suffix})"
        )
    if forecast_display_value in (None, "", "-"):
        return f"Obs {sanitize_text(observation_display_value)}{unit_suffix} vs forecast unavailable"
    return f"Obs {sanitize_text(observation_display_value)}{unit_suffix} vs Fcst {sanitize_text(forecast_display_value)}{unit_suffix}"


def _build_forecast_reason(
    *,
    forecast: dict,
    resolver: dict,
    comparison: dict,
    gate: dict,
    live_weather: dict,
) -> str:
    source_mode = str(
        forecast.get("source_mode")
        or forecast.get("forecast_status")
        or forecast.get("status")
        or ""
    ).strip()
    if not source_mode or source_mode == "-":
        source_mode = "forecast unavailable"
    source_mode_lower = source_mode.lower()
    if "target-date forecast unavailable" in source_mode_lower:
        return "Forecast row missing for target date."
    if "station mapping unavailable" in source_mode_lower:
        station_name = _first(resolver.get("station_name"), live_weather.get("station_name"), "-")
        return f"Resolver did not map a forecast source for station {sanitize_text(station_name)}."
    if "daily forecast matched" in source_mode_lower or "hourly fallback used" in source_mode_lower:
        return f"Forecast is available via {sanitize_text(source_mode)}."
    if "manual refresh" in source_mode_lower:
        return "Forecast was manually refreshed from the current live snapshot."
    if comparison.get("comparison_status") in {"market_mismatch", "unmatched_rule"}:
        return "Forecast exists, but it is not aligned to the selected market rule yet."
    if gate.get("execution_constraint") not in (None, "", "-"):
        return f"Forecast source mode is {sanitize_text(source_mode)}."
    return f"Forecast source mode is {sanitize_text(source_mode)}."


def _build_freshness_reason(
    *,
    validation_freshness_status: dict | None,
    gate: dict,
) -> str:
    freshness = validation_freshness_status if isinstance(validation_freshness_status, dict) else {}
    status = str(freshness.get("status") or gate.get("validation_freshness_status") or "").strip().lower()
    reason = str(freshness.get("reason") or "").strip()
    if status == "blocked" and reason:
        return f"Validation freshness is blocked because {reason.replace('_', ' ')}."
    if status == "blocked":
        return "Validation freshness is blocked by the freshness gate."
    if status == "warning":
        return "Validation freshness is aging and should be refreshed."
    if status == "healthy":
        return "Validation freshness is healthy."
    if str(gate.get("freshness_gate") or "").strip().lower() == "blocked":
        return "Freshness gate is blocked by upstream validation or label coverage."
    return "Freshness state is unavailable."


def _build_freshness_age(validation_freshness_status: dict | None) -> str:
    freshness = validation_freshness_status if isinstance(validation_freshness_status, dict) else {}
    freshness_seconds = freshness.get("freshness_seconds")
    if freshness_seconds in (None, ""):
        return "-"
    try:
        seconds = float(freshness_seconds)
    except Exception:
        return str(freshness_seconds)
    if seconds >= 3600:
        hours = seconds / 3600.0
        return f"{hours:.1f}h"
    if seconds >= 60:
        minutes = seconds / 60.0
        return f"{minutes:.0f}m"
    return f"{seconds:.0f}s"


def _as_float(value: object) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except Exception:
        return None


def _format_numeric(value: float) -> str:
    text = f"{value:.1f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def _format_signed_numeric(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{_format_numeric(value)}"


def _derive_market_probability(source: dict | None) -> float | None:
    source = source or {}
    explicit = _to_float(source.get("market_probability"))
    if explicit is not None:
        return round(explicit, 6)

    yes_price = _to_float(source.get("yes_price"))
    no_price = _to_float(source.get("no_price"))
    if yes_price is not None and no_price is not None:
        total = yes_price + no_price
        if total > 0:
            return round(max(0.0, min(1.0, yes_price / total)), 6)

    if yes_price is not None:
        return round(max(0.0, min(1.0, yes_price)), 6)

    if no_price is not None:
        return round(max(0.0, min(1.0, 1.0 - no_price)), 6)

    return None


def _build_top_parameter_compact_items(summary: TopParameterView) -> list[tuple[str, object]]:
    market_question = summary.get("market_question") or "-"
    market_family = summary.get("market_family") or "-"
    target_date = summary.get("target_date") or "-"
    market_id = summary.get("market_id") or "-"
    polymarket = summary.get("polymarket") or {}
    weather = summary.get("weather") or {}
    source_contract = summary.get("source_contract") or {}
    decision = summary.get("decision") or {}
    market_probability = polymarket.get("market_probability") or "-"
    weather_value = weather.get("display_value") or weather.get("weather_display_value") or weather.get("value") or "-"
    weather_unit = weather.get("display_unit") or weather.get("unit") or summary.get("canonical_unit") or "-"
    source_match_grade = source_contract.get("source_match_grade") or "-"
    freshness_status = source_contract.get("freshness_status") or "-"
    can_execute = decision.get("can_execute") or "-"
    block_reason = decision.get("primary_block_reason") or "-"
    recommended_action = decision.get("recommended_operator_action") or "-"
    return [
        ("Market", _shorten_summary_text(market_question, 42)),
        ("Market ID", market_id),
        ("Family", market_family),
        ("Target", target_date),
        ("Prob", market_probability),
        ("Weather", f"{weather_value} {weather_unit}".strip()),
        ("Source", source_match_grade),
        ("Fresh", freshness_status),
        ("Gate", can_execute),
        ("Block", _shorten_summary_text(block_reason, 34)),
        ("Action", _shorten_summary_text(recommended_action, 28)),
    ]


def _shorten_summary_text(value: object, max_len: int) -> str:
    text = sanitize_text(value)
    if max_len <= 0 or len(text) <= max_len:
        return text
    if max_len <= 1:
        return text[:max_len]
    return f"{text[: max_len - 1].rstrip()}…"


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _render_top_parameter_row(label: object, value: object) -> str:
    tone = semantic_tone(label, value)
    return (
        f"<div style='border-top:1px solid rgba(255,255,255,0.08);padding:0.12rem 0 0.10rem;margin-top:0.12rem;'>"
        f"<div style='color:#a3adb7;font-size:0.58rem;font-weight:850;letter-spacing:0.10em;"
        f"text-transform:uppercase;line-height:1.14;margin-bottom:0.04rem;'>{sanitize_text(label)}</div>"
        f"<div style='color:{_tone_color(tone)};font-size:0.82rem;font-weight:900;"
        f"line-height:1.20;font-variant-numeric:tabular-nums;word-break:break-word;"
        f"overflow-wrap:anywhere;white-space:normal;'>{sanitize_text(value)}</div>"
        f"</div>"
    )


def _is_empty_value(value: object) -> bool:
    return value in (None, "", "-", [], {})


def _tone_color(tone: str) -> str:
    return {
        "ok": "#8fe2b0",
        "warning": "#e6c67c",
        "critical": "#e5a09d",
        "neutral": "#f7fbff",
        "muted": "#a3adb7",
    }.get(tone, "#f7fbff")
