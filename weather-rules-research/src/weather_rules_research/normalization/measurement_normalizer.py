from __future__ import annotations

from typing import Any

from weather_rules_research.governance import normalize_measurement as _normalize_measurement


def normalize_measurement(
    value: Any,
    *,
    family: str | None = None,
    variable_name: str | None = None,
    raw_unit: str | None = None,
    band_scheme: str | None = None,
) -> dict[str, Any]:
    return _normalize_measurement(
        value,
        family=family,
        variable_name=variable_name,
        raw_unit=raw_unit,
        band_scheme=band_scheme,
    )


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
