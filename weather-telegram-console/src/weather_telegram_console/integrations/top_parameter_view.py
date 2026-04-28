from __future__ import annotations

import re

TOP_PARAMETER_VIEW_VERSION = "top_parameter_view.v1"


def build_top_parameter_view(
    *,
    current_market: dict | None,
    probability: dict | None = None,
    gate_stack: dict | None = None,
    resolver: dict | None = None,
    weather: dict | None = None,
    validation_freshness_status: dict | None = None,
) -> dict:
    current_market = current_market or {}
    probability = probability or {}
    gate_stack = gate_stack or {}
    resolver = resolver or {}
    weather = weather or {}

    market_id = _first(current_market.get("market_id"), "-")
    market_family = _first(current_market.get("market_family"), resolver.get("market_family"), "-")
    market_question = _first(current_market.get("market_question"), "-")
    location_name = _first(current_market.get("location_name"), resolver.get("location_name"), "-")
    target_date = _first(
        _normalize_market_question_target_date(market_question),
        current_market.get("target_date"),
        resolver.get("target_date"),
        "-",
    )
    variable_name = _first(current_market.get("variable_name"), resolver.get("variable_name"), "-")

    yes_price = _first(current_market.get("yes_price"), "-")
    no_price = _first(current_market.get("no_price"), "-")
    market_probability = _first(
        _derive_market_probability(current_market),
        probability.get("market_probability"),
        "-",
    )
    favored_side = _first(current_market.get("favored_side"), "-")
    market_band = _first(current_market.get("market_band"), current_market.get("market_band_label"), "-")
    spread = _first(current_market.get("spread"), current_market.get("market_spread"), "-")

    observation_value = _first(
        weather.get("observation_value"),
        weather.get("observed_temp_c"),
        current_market.get("observation_value"),
        "-",
    )
    observation_band = _first(
        weather.get("observation_band"),
        weather.get("official_band"),
        current_market.get("observation_band"),
        "-",
    )
    forecast_value = _first(
        weather.get("forecast_value"),
        current_market.get("forecast_value"),
        current_market.get("value"),
        "-",
    )
    unit = _first(weather.get("unit"), current_market.get("unit"), _infer_unit(market_family))
    model_band = _first(
        weather.get("model_band"),
        current_market.get("model_band"),
        resolver.get("expected_band"),
        "-",
    )
    station_name = _first(
        weather.get("station_name"),
        current_market.get("station_name"),
        resolver.get("station_name"),
        "-",
    )
    station_id = _first(
        weather.get("station_id"),
        weather.get("station_code"),
        current_market.get("station_id"),
        resolver.get("station_id"),
        "-",
    )
    observed_at = _first(
        weather.get("observed_at"),
        weather.get("observed_valid_time"),
        current_market.get("observed_at"),
        "-",
    )
    forecast_timestamp = _first(
        weather.get("forecast_timestamp"),
        current_market.get("forecast_timestamp"),
        current_market.get("timestamp"),
        "-",
    )
    source_confidence = _first(
        weather.get("source_confidence"),
        current_market.get("source_confidence"),
        probability.get("source_confidence"),
        "-",
    )
    settlement_ready = _first(
        weather.get("settlement_ready"),
        current_market.get("settlement_ready"),
        "-",
    )
    canonical_unit = _first(
        weather.get("canonical_unit"),
        resolver.get("canonical_unit"),
        unit,
    )
    source_priority = _first(
        resolver.get("source_priority"),
        current_market.get("source_priority"),
        probability.get("source_priority"),
        "-",
    )
    fallback_mode = _first(
        weather.get("source_mode"),
        resolver.get("fallback_mode"),
        resolver.get("fallback_policy"),
        "-",
    )
    source_policy_ref = _first(
        resolver.get("source_policy_ref"),
        current_market.get("source_policy_ref"),
        "-",
    )
    precision_policy_ref = _first(
        resolver.get("precision_policy_ref"),
        current_market.get("precision_policy_ref"),
        "-",
    )
    rounding_policy_ref = _first(
        resolver.get("rounding_policy_ref"),
        current_market.get("rounding_policy_ref"),
        "-",
    )
    band_mapping_policy_ref = _first(
        resolver.get("band_mapping_policy_ref"),
        current_market.get("band_mapping_policy_ref"),
        "-",
    )

    settlement_source_type = _first(
        resolver.get("settlement_source_type"),
        current_market.get("settlement_source_type"),
        "-",
    )
    official_vs_proxy_source = _first(
        resolver.get("official_vs_proxy_source"),
        current_market.get("official_vs_proxy_source"),
        "-",
    )
    source_match_grade = _first(
        resolver.get("source_match_grade"),
        current_market.get("source_match_grade"),
        "-",
    )
    required_sources = _join_list(
        resolver.get("required_sources") or current_market.get("required_sources")
    )
    official_source_url = _first(
        resolver.get("official_source_url"),
        current_market.get("official_source_url"),
        "-",
    )
    freshness_status = _first(
        gate_stack.get("validation_freshness_status"),
        gate_stack.get("freshness_gate"),
        "-",
    )

    fair_value = _first(probability.get("fair_value"), "-")
    edge = _first(probability.get("confidence_adjusted_edge"), probability.get("edge"), "-")
    probability_mode = _first(probability.get("probability_mode"), "-")
    execution_constraint = _first(probability.get("execution_constraint"), "-")
    can_execute = "yes" if str(gate_stack.get("execution_gate") or "").lower() == "pass" else "no"
    block_reasons = [str(item) for item in (gate_stack.get("block_reasons") or []) if item]
    primary_block_reason = block_reasons[0] if block_reasons else "none"
    recommended_operator_action = _first(
        gate_stack.get("recommended_operator_action"),
        current_market.get("action_hint"),
        "hold_execution_and_review",
    )
    comparison_status = _first(current_market.get("comparison_status"), "-")

    return {
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
            "spread": spread,
            "updated_at": _first(current_market.get("updated_at"), current_market.get("timestamp"), "-"),
        },
        "weather": {
            "observation_value": observation_value,
            "observation_band": observation_band,
            "forecast_value": forecast_value,
            "unit": unit,
            "canonical_unit": canonical_unit,
            "model_band": model_band,
            "official_band": _first(resolver.get("official_band"), "-"),
            "station_name": station_name,
            "station_id": station_id,
            "observed_at": observed_at,
            "forecast_timestamp": forecast_timestamp,
            "source_confidence": source_confidence,
            "settlement_ready": settlement_ready,
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
            "edge": edge,
            "probability_mode": probability_mode,
            "execution_constraint": execution_constraint,
            "can_execute": can_execute,
            "primary_block_reason": primary_block_reason,
            "recommended_operator_action": recommended_operator_action,
            "comparison_status": comparison_status,
        },
        "validation_freshness_status": validation_freshness_status or {},
    }


def _first(*values: object) -> object:
    for value in values:
        if value not in (None, ""):
            return value
    return "-"


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


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _join_list(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if item not in (None, ""))
    if value not in (None, ""):
        return str(value)
    return "-"


def _infer_unit(market_family: str) -> str:
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
