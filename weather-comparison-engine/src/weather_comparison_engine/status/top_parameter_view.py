from __future__ import annotations

import re

from weather_comparison_engine.governance import normalize_measurement

TOP_PARAMETER_VIEW_SCHEMA_VERSION = "top_parameter_view.v2"


def build_top_parameter_view(
    *,
    current_market: dict | None,
    forecast_snapshot: dict | None = None,
    comparison_point: dict | None = None,
) -> dict:
    current_market = current_market or {}
    forecast_snapshot = forecast_snapshot or {}
    comparison_point = comparison_point or {}

    market_family = str(
        current_market.get("market_family")
        or forecast_snapshot.get("market_family")
        or comparison_point.get("market_family")
        or "-"
    )
    market_id = _first(
        current_market.get("market_id"),
        comparison_point.get("market_id"),
        forecast_snapshot.get("market_id"),
        "-",
    )
    market_question = _first(
        current_market.get("market_question"),
        comparison_point.get("market_question"),
        forecast_snapshot.get("market_question"),
        "-",
    )
    location_name = _first(
        current_market.get("location_name"),
        forecast_snapshot.get("location_name"),
        comparison_point.get("location_name"),
        "-",
    )
    target_date = _first(
        _normalize_market_question_target_date(market_question),
        current_market.get("target_date"),
        forecast_snapshot.get("target_date"),
        comparison_point.get("target_date"),
        "-",
    )
    variable_name = _first(
        current_market.get("variable_name"),
        forecast_snapshot.get("variable_name"),
        comparison_point.get("variable_name"),
        "-",
    )

    market_probability = _first(
        _derive_market_probability(current_market),
        _derive_market_probability(comparison_point),
        "-",
    )
    yes_price = _first(current_market.get("yes_price"), comparison_point.get("yes_price"), "-")
    no_price = _first(current_market.get("no_price"), comparison_point.get("no_price"), "-")
    favored_side = _first(current_market.get("favored_side"), comparison_point.get("favored_side"), "-")
    market_band = _first(
        current_market.get("market_band"),
        current_market.get("market_band_label"),
        comparison_point.get("market_band"),
        "-",
    )

    observation_measurement = _normalize_measurement_bundle(
        value=_first(
            forecast_snapshot.get("observed_value"),
            forecast_snapshot.get("observation_value"),
            current_market.get("observation_value"),
            "-",
        ),
        family=market_family,
        variable_name=variable_name,
        raw_unit=_first(
            forecast_snapshot.get("raw_unit"),
            current_market.get("raw_unit"),
            forecast_snapshot.get("unit"),
            current_market.get("unit"),
            _infer_unit(market_family),
        ),
        band_scheme=_first(
            forecast_snapshot.get("band_scheme"),
            current_market.get("band_scheme"),
            comparison_point.get("band_scheme"),
            "-",
        ),
    )
    forecast_measurement = _normalize_measurement_bundle(
        value=_first(
            forecast_snapshot.get("forecast_value"),
            forecast_snapshot.get("value"),
            current_market.get("forecast_value"),
            comparison_point.get("model_value"),
            "-",
        ),
        family=market_family,
        variable_name=variable_name,
        raw_unit=_first(
            forecast_snapshot.get("raw_unit"),
            current_market.get("raw_unit"),
            forecast_snapshot.get("unit"),
            current_market.get("unit"),
            _infer_unit(market_family),
        ),
        band_scheme=_first(
            forecast_snapshot.get("band_scheme"),
            current_market.get("band_scheme"),
            comparison_point.get("band_scheme"),
            "-",
        ),
    )

    observation_value = observation_measurement["display_value"]
    forecast_value = forecast_measurement["display_value"]
    unit = _first(
        forecast_measurement["display_unit"],
        forecast_snapshot.get("unit"),
        current_market.get("unit"),
        _infer_unit(market_family),
    )
    canonical_unit = _first(
        forecast_measurement["canonical_unit"],
        forecast_snapshot.get("canonical_unit"),
        current_market.get("canonical_unit"),
        unit,
    )
    model_band = _first(
        forecast_snapshot.get("model_band"),
        current_market.get("model_band"),
        comparison_point.get("model_band"),
        "-",
    )
    official_band = _first(current_market.get("official_band"), forecast_snapshot.get("official_band"), "-")
    station_name = _first(
        forecast_snapshot.get("station_name"),
        current_market.get("station_name"),
        "-",
    )
    station_id = _first(
        forecast_snapshot.get("station_id"),
        forecast_snapshot.get("station_code"),
        current_market.get("station_id"),
        "-",
    )
    observed_at = _first(
        forecast_snapshot.get("observed_at"),
        forecast_snapshot.get("observed_valid_time"),
        current_market.get("observed_at"),
        "-",
    )
    forecast_timestamp = _first(
        forecast_snapshot.get("forecast_timestamp"),
        forecast_snapshot.get("timestamp"),
        current_market.get("forecast_timestamp"),
        "-",
    )
    source_mode = _first(forecast_snapshot.get("source_mode"), "-")
    required_data_source = _first(
        forecast_snapshot.get("required_data_source"),
        comparison_point.get("required_data_source"),
        current_market.get("required_data_source"),
        "-",
    )
    source_priority = _first(
        comparison_point.get("source_priority"),
        forecast_snapshot.get("source_priority"),
        current_market.get("source_priority"),
        "-",
    )
    fallback_mode = _first(
        forecast_snapshot.get("source_mode"),
        comparison_point.get("fallback_mode"),
        comparison_point.get("fallback_policy"),
        "-",
    )
    precision_policy_ref = _first(
        forecast_measurement["precision_policy_ref"],
        comparison_point.get("precision_policy_ref"),
        forecast_snapshot.get("precision_policy_ref"),
        current_market.get("precision_policy_ref"),
        "-",
    )
    rounding_policy_ref = _first(
        forecast_measurement["rounding_policy_ref"],
        comparison_point.get("rounding_policy_ref"),
        forecast_snapshot.get("rounding_policy_ref"),
        current_market.get("rounding_policy_ref"),
        "-",
    )
    band_mapping_policy_ref = _first(
        forecast_measurement["band_mapping_policy_ref"],
        comparison_point.get("band_mapping_policy_ref"),
        forecast_snapshot.get("band_mapping_policy_ref"),
        current_market.get("band_mapping_policy_ref"),
        "-",
    )
    source_policy_ref = _first(
        comparison_point.get("source_policy_ref"),
        forecast_snapshot.get("source_policy_ref"),
        current_market.get("source_policy_ref"),
        "-",
    )

    settlement_source_type = _first(
        forecast_snapshot.get("settlement_source_type"),
        current_market.get("settlement_source_type"),
        "-",
    )
    official_vs_proxy_source = _first(
        forecast_snapshot.get("official_vs_proxy_source"),
        current_market.get("official_vs_proxy_source"),
        "-",
    )
    source_match_grade = _first(
        forecast_snapshot.get("source_match_grade"),
        current_market.get("source_match_grade"),
        comparison_point.get("source_match_grade"),
        "-",
    )
    required_sources = _join_list(
        forecast_snapshot.get("required_sources")
        or current_market.get("required_sources")
        or comparison_point.get("required_sources")
    )
    official_source_url = _first(
        forecast_snapshot.get("official_source_url"),
        current_market.get("official_source_url"),
        "-",
    )
    freshness_status = _first(
        forecast_snapshot.get("freshness_status"),
        current_market.get("freshness_status"),
        "-",
    )

    fair_value = _first(comparison_point.get("fair_value"), "-")
    edge = _first(
        comparison_point.get("confidence_adjusted_edge"),
        comparison_point.get("confidence_adjusted_gap"),
        comparison_point.get("edge"),
        "-",
    )
    probability_mode = _first(comparison_point.get("probability_mode"), "-")
    execution_constraint = _first(comparison_point.get("execution_constraint"), "-")
    can_execute = _bool_to_yes_no(comparison_point.get("can_execute"))
    block_reasons = [str(item) for item in (comparison_point.get("block_reasons") or []) if item]
    primary_block_reason = _first(
        comparison_point.get("primary_block_reason"),
        block_reasons[0] if block_reasons else "none",
    )
    recommended_operator_action = _first(
        comparison_point.get("recommended_operator_action"),
        comparison_point.get("action_hint"),
        "hold_execution_and_review",
    )
    comparison_status = _first(comparison_point.get("comparison_status"), "-")

    return {
        "schema_version": TOP_PARAMETER_VIEW_SCHEMA_VERSION,
        "market_id": market_id,
        "market_family": market_family,
        "market_question": market_question,
        "location_name": location_name,
        "target_date": target_date,
        "variable_name": variable_name,
        "canonical_unit": canonical_unit,
        "source_priority": source_priority,
        "fallback_mode": fallback_mode,
        "policy_refs": {
            "source_policy_ref": source_policy_ref,
            "precision_policy_ref": precision_policy_ref,
            "rounding_policy_ref": rounding_policy_ref,
            "band_mapping_policy_ref": band_mapping_policy_ref,
        },
        "polymarket": {
            "yes_price": yes_price,
            "no_price": no_price,
            "market_implied_probability": market_probability,
            "display_market_probability": market_probability,
            "favored_side": favored_side,
            "market_band": market_band,
        },
        "forecast": {
            **forecast_measurement,
            "forecast_value": forecast_value,
            "forecast_raw_value": forecast_measurement["raw_value"],
            "forecast_raw_unit": forecast_measurement["raw_unit"],
            "forecast_canonical_value": forecast_measurement["canonical_value"],
            "forecast_canonical_unit": forecast_measurement["canonical_unit"],
            "forecast_display_value": forecast_value,
            "forecast_display_unit": forecast_measurement["display_unit"],
            "forecast_timestamp": forecast_timestamp,
            "source_mode": source_mode,
            "required_data_source": required_data_source,
        },
        "weather": {
            **observation_measurement,
            "observation_value": observation_value,
            "observation_raw_value": observation_measurement["raw_value"],
            "observation_raw_unit": observation_measurement["raw_unit"],
            "observation_canonical_value": observation_measurement["canonical_value"],
            "observation_canonical_unit": observation_measurement["canonical_unit"],
            "observation_display_value": observation_value,
            "observation_display_unit": observation_measurement["display_unit"],
            "observation_band": _first(current_market.get("observation_band"), "-"),
            "forecast_value": forecast_value,
            "forecast_raw_value": forecast_measurement["raw_value"],
            "forecast_raw_unit": forecast_measurement["raw_unit"],
            "forecast_canonical_value": forecast_measurement["canonical_value"],
            "forecast_canonical_unit": forecast_measurement["canonical_unit"],
            "forecast_display_value": forecast_value,
            "forecast_display_unit": forecast_measurement["display_unit"],
            "unit": unit,
            "model_band": model_band,
            "official_band": official_band,
            "station_name": station_name,
            "station_id": station_id,
            "observed_at": observed_at,
            "forecast_timestamp": forecast_timestamp,
            "source_mode": source_mode,
            "required_data_source": required_data_source,
            "settlement_ready": _first(current_market.get("settlement_ready"), "-"),
            "normalization_version": forecast_measurement["normalization_version"],
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
        "normalization": {
            "raw_unit": forecast_measurement["raw_unit"],
            "canonical_unit": canonical_unit,
            "display_unit": forecast_measurement["display_unit"],
            "raw_value": forecast_measurement["raw_value"],
            "canonical_value": forecast_measurement["canonical_value"],
            "display_value": forecast_measurement["display_value"],
            "conversion_rule": forecast_measurement["conversion_rule"],
            "conversion_applied": forecast_measurement["conversion_applied"],
            "precision_policy_ref": precision_policy_ref,
            "rounding_policy_ref": rounding_policy_ref,
            "band_mapping_policy_ref": band_mapping_policy_ref,
            "normalization_version": forecast_measurement["normalization_version"],
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


def _normalize_measurement_bundle(
    *,
    value: object,
    family: str,
    variable_name: str,
    raw_unit: object = None,
    band_scheme: object = None,
) -> dict[str, object]:
    normalized = normalize_measurement(
        {"raw_value": value, "raw_unit": raw_unit},
        family=family,
        variable_name=variable_name,
        raw_unit=str(raw_unit) if raw_unit not in (None, "") else None,
        band_scheme=str(band_scheme) if band_scheme not in (None, "") else None,
    )
    return {
        "raw_value": normalized.get("raw_value"),
        "raw_unit": normalized.get("raw_unit"),
        "canonical_value": normalized.get("canonical_value"),
        "canonical_unit": normalized.get("canonical_unit"),
        "display_value": _first(normalized.get("display_value"), normalized.get("canonical_value"), value, "-"),
        "display_unit": normalized.get("display_unit"),
        "conversion_rule": normalized.get("conversion_rule"),
        "conversion_applied": normalized.get("conversion_applied"),
        "precision_policy_ref": normalized.get("precision_policy_ref"),
        "rounding_policy_ref": normalized.get("rounding_policy_ref"),
        "band_mapping_policy_ref": normalized.get("band_mapping_policy_ref"),
        "normalization_version": normalized.get("normalization_version"),
    }


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


def _bool_to_yes_no(value: object) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
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
