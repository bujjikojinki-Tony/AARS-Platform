from __future__ import annotations

import re
from datetime import date


_MONTH_ALIASES = {
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

_DATE_PATTERNS = (
    re.compile(
        r"\b(?P<month>jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
        r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sept?(?:ember)?|oct(?:ober)?|"
        r"nov(?:ember)?|dec(?:ember)?)\.?\s+(?P<day>\d{1,2})(?:,\s*(?P<year>\d{4}))?\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\b"),
)


def build_latest_dashboard_row(
    *,
    market_snapshot: dict,
    forecast_snapshot: dict,
    point: dict,
) -> dict:
    market_question = market_snapshot.get("market_question")
    normalized_target_date = normalize_market_target_date(market_question)
    target_date_source = "market_question" if normalized_target_date else "forecast_snapshot"

    return {
        "market_id": market_snapshot["market_id"],
        "market_question": market_snapshot.get("market_question"),
        "location_name": market_snapshot.get("location_name", "UNKNOWN"),
        "target_date": normalized_target_date or forecast_snapshot.get("target_date"),
        "target_date_source": target_date_source,
        "question_target_date": normalized_target_date,
        "variable_name": forecast_snapshot.get("variable_name"),
        "market_probability": _derive_market_probability(market_snapshot),
        "favored_side": market_snapshot.get("favored_side"),
        "yes_price": market_snapshot.get("yes_price"),
        "no_price": market_snapshot.get("no_price"),
        "model_value": point.get("model_value"),
        "model_display_value": point.get("model_display_value"),
        "model_canonical_value": point.get("model_canonical_value"),
        "model_raw_value": point.get("model_raw_value"),
        "model_band": point.get("model_band"),
        "market_band": point.get("market_band"),
        "band_scheme": point.get("band_scheme"),
        "market_band_scheme": point.get("market_band_scheme"),
        "forecast_raw_value": forecast_snapshot.get("raw_value"),
        "forecast_canonical_value": forecast_snapshot.get("canonical_value"),
        "forecast_display_value": forecast_snapshot.get("display_value"),
        "forecast_raw_unit": forecast_snapshot.get("raw_unit"),
        "forecast_canonical_unit": forecast_snapshot.get("canonical_unit"),
        "forecast_display_unit": forecast_snapshot.get("display_unit"),
        "forecast_conversion_rule": forecast_snapshot.get("conversion_rule"),
        "forecast_conversion_applied": forecast_snapshot.get("conversion_applied"),
        "forecast_precision_policy_ref": forecast_snapshot.get("precision_policy_ref"),
        "forecast_rounding_policy_ref": forecast_snapshot.get("rounding_policy_ref"),
        "forecast_band_mapping_policy_ref": forecast_snapshot.get("band_mapping_policy_ref"),
        "forecast_market_id": forecast_snapshot.get("market_id"),
        "rule_status": point.get("rule_status"),
        "rule_market_id": point.get("rule_market_id"),
        "market_family": point.get("market_family"),
        "resolution_scope": point.get("resolution_scope"),
        "supported_by_current_pipeline": point.get("supported_by_current_pipeline"),
        "required_data_source": point.get("required_data_source"),
        "band_distance": 0 if point.get("comparison_status") == "aligned" else (
            1 if point.get("comparison_status") == "mild_divergence" else 2
        ),
        "confidence_score": point.get("confidence_score"),
        "confidence_adjusted_gap": point.get("confidence_adjusted_gap"),
        "comparison_status": point.get("comparison_status"),
        "action_hint": point.get("action_hint"),
        "market_snapshot_ref": point.get("market_snapshot_ref"),
        "forecast_snapshot_ref": point.get("forecast_snapshot_ref"),
        "forecast_snapshot_normalization_version": forecast_snapshot.get("normalization_version"),
        "comparison_reason": point.get("comparison_reason"),
    }


def normalize_market_target_date(market_question: str | None) -> str | None:
    if not market_question:
        return None
    text = str(market_question).strip()
    if not text:
        return None

    for pattern in _DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        groups = match.groupdict()
        if "month" in groups and groups.get("month"):
            month_key = groups["month"].lower().rstrip(".")
            month = _MONTH_ALIASES.get(month_key)
            day = int(groups["day"])
            if month:
                return f"{month} {day}"
        if groups.get("year") and groups.get("month") and groups.get("day"):
            try:
                normalized = date(
                    int(groups["year"]),
                    int(groups["month"]),
                    int(groups["day"]),
                )
            except ValueError:
                continue
            return f"{normalized.strftime('%b')} {normalized.day}"
    return None


def _derive_market_probability(market_snapshot: dict) -> float | None:
    explicit = _to_float(market_snapshot.get("market_probability"))
    if explicit is not None:
        return round(explicit, 6)

    yes_price = _to_float(market_snapshot.get("yes_price"))
    no_price = _to_float(market_snapshot.get("no_price"))
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
