from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from weather_comparison_engine.governance.measurement_policy_loader import (
    get_band_mapping_policy_for_scheme,
    get_precision_policy_for_family,
    get_rounding_policy_for_family,
    get_unit_policy_for_family,
)


def normalize_measurement(
    value: Any,
    *,
    family: str | None = None,
    variable_name: str | None = None,
    raw_unit: str | None = None,
    band_scheme: str | None = None,
) -> dict[str, Any]:
    raw_value = _extract_raw_value(value)
    raw_unit = raw_unit or _extract_raw_unit(value)
    family = str(family or _extract_family(value) or "").strip()
    variable_name = str(variable_name or _extract_variable_name(value) or "").strip()
    canonical_unit = _resolve_canonical_unit(family, value)
    precision_policy = get_precision_policy_for_family(family)
    rounding_policy = get_rounding_policy_for_family(family)
    band_mapping_policy = get_band_mapping_policy_for_scheme(band_scheme or _extract_band_scheme(value) or "")
    unit_policy = get_unit_policy_for_family(family)

    canonical_value = _to_float(raw_value)
    if canonical_value is not None:
        canonical_value = _convert_to_canonical(
            canonical_value,
            raw_unit=raw_unit,
            canonical_unit=str(canonical_unit or unit_policy.get("canonical_unit") or raw_unit or "-"),
        )
        canonical_value = _round_numeric(
            canonical_value,
            precision=_comparison_precision(precision_policy),
            rounding_rule=_rounding_rule(rounding_policy, "threshold_compare"),
        )

    display_value = canonical_value
    if display_value is not None:
        display_value = _round_numeric(
            display_value,
            precision=_display_precision(precision_policy),
            rounding_rule=_rounding_rule(rounding_policy, "display"),
        )

    return {
        "raw_value": raw_value,
        "raw_unit": raw_unit,
        "canonical_value": canonical_value,
        "canonical_unit": canonical_unit or unit_policy.get("canonical_unit") or raw_unit or "-",
        "display_value": display_value,
        "display_unit": unit_policy.get("display_unit") or canonical_unit or raw_unit or "-",
        "family": family or "-",
        "variable_name": variable_name or "-",
        "precision_policy_ref": precision_policy.get("policy_id") or "-",
        "rounding_policy_ref": rounding_policy.get("policy_id") or "-",
        "band_mapping_policy_ref": band_mapping_policy.get("policy_id") or "-",
        "normalization_version": "measurement_normalization.v1",
    }


def get_canonical_value(
    value: Any,
    *,
    family: str | None = None,
    variable_name: str | None = None,
    raw_unit: str | None = None,
    band_scheme: str | None = None,
) -> Any:
    return normalize_measurement(
        value,
        family=family,
        variable_name=variable_name,
        raw_unit=raw_unit,
        band_scheme=band_scheme,
    ).get("canonical_value")


def get_display_value(
    value: Any,
    *,
    family: str | None = None,
    variable_name: str | None = None,
    raw_unit: str | None = None,
    band_scheme: str | None = None,
) -> Any:
    return normalize_measurement(
        value,
        family=family,
        variable_name=variable_name,
        raw_unit=raw_unit,
        band_scheme=band_scheme,
    ).get("display_value")


def get_band_mapping_policy(
    family_or_band_scheme: str,
) -> dict[str, Any]:
    policy = get_band_mapping_policy_for_scheme(family_or_band_scheme)
    if policy:
        return policy
    return get_band_mapping_policy_for_scheme(str(family_or_band_scheme or "").strip().lower())


def _extract_raw_value(value: Any) -> Any:
    if isinstance(value, dict):
        for key in ("raw_value", "canonical_value", "value"):
            if key in value and value.get(key) not in (None, ""):
                return value.get(key)
    return value


def _extract_raw_unit(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ("raw_unit", "unit", "display_unit", "canonical_unit"):
            raw_unit = value.get(key)
            if raw_unit not in (None, ""):
                return str(raw_unit)
    return None


def _extract_family(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ("family", "market_family"):
            family = value.get(key)
            if family not in (None, ""):
                return str(family)
    return None


def _extract_variable_name(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ("variable_name", "variable"):
            variable_name = value.get(key)
            if variable_name not in (None, ""):
                return str(variable_name)
    return None


def _extract_band_scheme(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ("band_scheme", "market_band_scheme"):
            band_scheme = value.get(key)
            if band_scheme not in (None, ""):
                return str(band_scheme)
    return None


def _resolve_canonical_unit(family: str, value: Any) -> str | None:
    if isinstance(value, dict):
        canonical_unit = value.get("canonical_unit")
        if canonical_unit not in (None, ""):
            return str(canonical_unit)
    if family:
        policy = get_precision_policy_for_family(family)
        if policy.get("canonical_unit") not in (None, ""):
            return str(policy.get("canonical_unit"))
    return None


def _comparison_precision(policy: dict[str, Any]) -> int | None:
    precision = policy.get("comparison_precision")
    if isinstance(precision, int):
        return precision
    try:
        return int(precision)
    except (TypeError, ValueError):
        return None


def _display_precision(policy: dict[str, Any]) -> int | None:
    precision = policy.get("display_precision")
    if isinstance(precision, int):
        return precision
    try:
        return int(precision)
    except (TypeError, ValueError):
        return None


def _rounding_rule(policy: dict[str, Any], applies_to: str) -> str:
    for rule in policy.get("rules") or []:
        if isinstance(rule, dict) and str(rule.get("applies_to") or "") == applies_to:
            return str(rule.get("rounding_rule") or "exact_no_rounding")
    return "exact_no_rounding"


def _convert_to_canonical(value: float, *, raw_unit: str | None, canonical_unit: str | None) -> float:
    raw = str(raw_unit or "").strip().lower()
    canonical = str(canonical_unit or "").strip().lower()
    if not raw or raw == canonical:
        return value

    if canonical == "celsius":
        if raw == "fahrenheit":
            return (value - 32.0) * (5.0 / 9.0)
        return value
    if canonical == "kt":
        if raw == "mph":
            return value * 0.868976
        if raw in {"m/s", "ms"}:
            return value * 1.943844
        if raw == "km/h":
            return value * 0.539957
        return value
    if canonical == "mm":
        if raw == "inch":
            return value * 25.4
        if raw == "cm":
            return value * 10.0
        return value
    return value


def _round_numeric(value: float, *, precision: int | None, rounding_rule: str) -> float:
    if precision is None or rounding_rule == "exact_no_rounding":
        return value
    quantize = Decimal("1").scaleb(-precision)
    decimal_value = Decimal(str(value))
    return float(decimal_value.quantize(quantize, rounding=ROUND_HALF_UP))


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
