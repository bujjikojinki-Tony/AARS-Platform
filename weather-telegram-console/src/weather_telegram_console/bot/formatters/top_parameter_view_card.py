from __future__ import annotations

from weather_telegram_console.bot.formatters.telegram_text import md_line
from weather_telegram_console.bot.formatters.top_parameter_family_profiles import (
    get_family_top_parameter_profile,
)


def format_top_parameter_view_card(view: dict | None) -> str:
    view = view or {}
    polymarket = view.get("polymarket") if isinstance(view.get("polymarket"), dict) else {}
    forecast = view.get("forecast") if isinstance(view.get("forecast"), dict) else {}
    weather = view.get("weather") if isinstance(view.get("weather"), dict) else {}
    source_contract = view.get("source_contract") if isinstance(view.get("source_contract"), dict) else {}
    decision = view.get("decision") if isinstance(view.get("decision"), dict) else {}
    validation = view.get("validation_freshness_status") if isinstance(view.get("validation_freshness_status"), dict) else {}
    family_profile = get_family_top_parameter_profile(view.get("market_family"))

    compare_value = _build_realtime_compare_value(weather, forecast, family_profile)
    forecast_reason = _build_forecast_reason(forecast, source_contract, decision, weather)
    freshness_reason = _build_freshness_reason(validation, source_contract)
    freshness_age = _build_freshness_age(validation)
    weather_metric_label = "Live Temp vs Forecast"
    weather_metric_value = compare_value if compare_value != "-" else _first(
        weather.get("forecast_display_value"),
        weather.get("forecast_value"),
        forecast.get("forecast_display_value"),
        forecast.get("forecast_value"),
        "unavailable",
    )

    sections = [
        ("*Market Identity*", [
            ("Market ID", view.get("market_id")),
            ("Question", view.get("market_question")),
            ("Market Family", view.get("market_family")),
            ("Location", view.get("location_name")),
            ("Target Date", view.get("target_date")),
            ("Variable", view.get("variable_name")),
        ]),
        ("*Polymarket Params*", [
            ("YES Price", polymarket.get("yes_price")),
            ("NO Price", polymarket.get("no_price")),
            ("Market Probability", _first(polymarket.get("display_market_probability"), polymarket.get("market_implied_probability"))),
            ("Favored Side", polymarket.get("favored_side")),
            ("Market Band", polymarket.get("market_band")),
            ("Spread", polymarket.get("spread")),
            ("Updated At", polymarket.get("updated_at")),
        ]),
        ("*Weather / Forecast Params*", [
            (family_profile.get("observation_label", "Observation"), _first(weather.get("observation_display_value"), weather.get("observation_value"))),
            (family_profile.get("forecast_label", "Forecast"), _first(weather.get("forecast_display_value"), weather.get("forecast_value"), forecast.get("forecast_display_value"), forecast.get("forecast_value"))),
            (weather_metric_label, weather_metric_value),
            ("Forecast Reason", forecast_reason),
            ("Freshness Reason", freshness_reason),
            ("Freshness Age", freshness_age),
            ("Unit", _first(weather.get("display_unit"), weather.get("unit"))),
            ("Canonical Unit", weather.get("canonical_unit")),
            ("Model Band", weather.get("model_band")),
            ("Official Band", weather.get("official_band")),
            ("Station", weather.get("station_name")),
            ("Station ID", weather.get("station_id")),
            ("Observed At", weather.get("observed_at")),
            ("Forecast Timestamp", weather.get("forecast_timestamp")),
            ("Settlement Ready", weather.get("settlement_ready")),
            ("Raw Observation", _first(weather.get("observation_raw_value"), forecast.get("observation_raw_value"))),
            ("Canonical Observation", _first(weather.get("observation_canonical_value"), forecast.get("observation_canonical_value"))),
            ("Raw Forecast", _first(weather.get("forecast_raw_value"), forecast.get("forecast_raw_value"))),
            ("Canonical Forecast", _first(weather.get("forecast_canonical_value"), forecast.get("forecast_canonical_value"))),
        ]),
        ("*Resolver / Source Contract*", [
            ("Settlement Source Type", source_contract.get("settlement_source_type")),
            ("Official vs Proxy", source_contract.get("official_vs_proxy_source")),
            ("Source Match Grade", source_contract.get("source_match_grade")),
            ("Required Sources", source_contract.get("required_sources")),
            ("Official Source URL", source_contract.get("official_source_url")),
            ("Freshness Status", source_contract.get("freshness_status")),
            ("Source Priority", source_contract.get("source_priority")),
            ("Fallback Mode", source_contract.get("fallback_mode")),
            ("Source Policy Ref", source_contract.get("source_policy_ref")),
            ("Precision Policy Ref", source_contract.get("precision_policy_ref")),
            ("Rounding Policy Ref", source_contract.get("rounding_policy_ref")),
            ("Band Mapping Policy Ref", source_contract.get("band_mapping_policy_ref")),
        ]),
        ("*Comparison / Gate Summary*", [
            ("Fair Value", decision.get("fair_value")),
            ("Edge", decision.get("edge")),
            ("Probability Mode", decision.get("probability_mode")),
            ("Execution Constraint", decision.get("execution_constraint")),
            ("Can Execute", decision.get("can_execute")),
            ("Primary Block Reason", decision.get("primary_block_reason")),
            ("Recommended Action", decision.get("recommended_operator_action")),
            ("Comparison Status", decision.get("comparison_status")),
            ("Freshness Status", source_contract.get("freshness_status")),
            ("Freshness Reason", freshness_reason),
        ]),
    ]

    rendered_sections: list[str] = ["*Top Parameter Surface*"]
    for title, rows in sections:
        rendered = _render_section(title, rows)
        if rendered:
            rendered_sections.append(rendered)

    return "\n\n".join(rendered_sections) + "\n"


def _render_section(title: str, rows: list[tuple[str, object]]) -> str:
    rendered_rows = []
    for label, value in rows:
        if _is_empty_value(value):
            continue
        rendered_rows.append(md_line(label, value))
    if not rendered_rows:
        return ""
    return "\n".join([title, *rendered_rows])


def _is_empty_value(value: object) -> bool:
    return value in (None, "", "-", [], {})


def _first(*values: object) -> object:
    for value in values:
        if value not in (None, ""):
            return value
    return "-"


def _build_realtime_compare_value(weather: dict, forecast: dict, family_profile: dict) -> str:
    observation = _first(weather.get("observation_display_value"), weather.get("observation_value"))
    forecast_value = _first(
        weather.get("forecast_display_value"),
        weather.get("forecast_value"),
        forecast.get("forecast_display_value"),
        forecast.get("forecast_value"),
    )
    obs_num = _as_float(_first(weather.get("observation_canonical_value"), weather.get("observation_value")))
    fcst_num = _as_float(_first(weather.get("forecast_canonical_value"), weather.get("forecast_value")))
    unit = _first(weather.get("display_unit"), weather.get("unit"), family_profile.get("unit"))
    unit_suffix = f" {unit}" if unit not in (None, "", "-") else ""
    if obs_num is not None and fcst_num is not None:
        delta = obs_num - fcst_num
        return (
            f"Obs { _format_num(obs_num) }{unit_suffix} vs "
            f"Fcst { _format_num(fcst_num) }{unit_suffix} "
            f"(Δ {_format_signed_num(delta)}{unit_suffix})"
        )
    if forecast_value in (None, "", "-"):
        return f"Obs {observation}{unit_suffix} vs forecast unavailable"
    return f"Obs {observation}{unit_suffix} vs Fcst {forecast_value}{unit_suffix}"


def _build_forecast_reason(forecast: dict, source_contract: dict, decision: dict, weather: dict) -> str:
    source_mode = str(
        forecast.get("source_mode")
        or forecast.get("forecast_status")
        or decision.get("comparison_status")
        or ""
    ).strip()
    lower = source_mode.lower()
    if "target-date forecast unavailable" in lower:
        return "Forecast row missing for target date."
    if "station mapping unavailable" in lower:
        station = _first(weather.get("station_name"), source_contract.get("station_name"), "-")
        return f"Resolver did not map a forecast source for station {station}."
    if source_mode and source_mode != "-":
        return f"Forecast source mode is {source_mode}."
    return "Forecast status unavailable."


def _build_freshness_reason(validation: dict, source_contract: dict) -> str:
    status = str(validation.get("status") or source_contract.get("freshness_status") or "").strip().lower()
    reason = str(validation.get("reason") or "").strip()
    if status == "blocked" and reason:
        return f"Validation freshness is blocked because {reason.replace('_', ' ')}."
    if status == "blocked":
        return "Validation freshness is blocked by the freshness gate."
    if status == "warning":
        return "Validation freshness is aging and should be refreshed."
    if status == "healthy":
        return "Validation freshness is healthy."
    if status:
        return f"Freshness status is {status}."
    return "Freshness state is unavailable."


def _build_freshness_age(validation: dict) -> str:
    freshness_seconds = validation.get("freshness_seconds")
    if freshness_seconds in (None, ""):
        return "-"
    try:
        seconds = float(freshness_seconds)
    except Exception:
        return str(freshness_seconds)
    if seconds >= 3600:
        return f"{seconds / 3600.0:.1f}h"
    if seconds >= 60:
        return f"{seconds / 60.0:.0f}m"
    return f"{seconds:.0f}s"


def _as_float(value: object) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except Exception:
        return None


def _format_num(value: float) -> str:
    text = f"{value:.1f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def _format_signed_num(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{_format_num(value)}"
