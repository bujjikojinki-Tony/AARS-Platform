from __future__ import annotations

from typing import Any

from weather_rules_research.governance.measurement_policy_loader import (
    load_measurement_registry_bundle,
)


VARIABLE_GROUP_BY_VARIABLE_NAME: dict[str, str] = {
    "daily_max_temperature": "temperature",
    "daily_min_temperature": "temperature",
    "daily_precipitation_sum": "precipitation",
    "daily_snowfall_sum": "snowfall",
    "daily_max_wind_speed": "wind_speed",
}

POLICY_FAMILY_BY_VARIABLE_NAME: dict[str, str] = {
    "daily_max_temperature": "temperature_daily_max",
    "daily_min_temperature": "temperature_daily_min",
    "daily_precipitation_sum": "weather_metric.precipitation",
    "daily_snowfall_sum": "weather_metric.snowfall",
    "daily_max_wind_speed": "weather_metric.wind_speed",
}

SOURCE_POLICY_BY_FAMILY: dict[str, str] = {
    "station_temperature": "wunderground_station",
    "weather_metric": "wunderground_station",
    "sea_ice_extent": "sea_ice_dataset",
    "global_temperature_index": "climate_index_source",
}


def build_policy_refs(
    *,
    market_family: str | None,
    variable_name: str | None,
    band_scheme: str | None,
    source_policy_ref: str | None = None,
) -> dict[str, str | None]:
    bundle = load_measurement_registry_bundle()
    resolved_source_policy_ref = source_policy_ref or SOURCE_POLICY_BY_FAMILY.get(str(market_family or ""))
    variable_group = _variable_group_for(variable_name=variable_name, market_family=market_family)
    policy_family = _policy_family_for(variable_name=variable_name, market_family=market_family)
    unit_policy_ref = variable_group
    precision_policy_ref = _find_precision_policy_ref(
        bundle=bundle,
        policy_family=policy_family,
        variable_name=variable_name,
    )
    rounding_policy_ref = _find_rounding_policy_ref(
        bundle=bundle,
        policy_family=policy_family,
    )
    band_mapping_policy_ref = _find_band_mapping_policy_ref(
        bundle=bundle,
        band_scheme=band_scheme,
    )
    return {
        "source_policy_ref": resolved_source_policy_ref,
        "unit_policy_ref": unit_policy_ref,
        "precision_policy_ref": precision_policy_ref,
        "rounding_policy_ref": rounding_policy_ref,
        "band_mapping_policy_ref": band_mapping_policy_ref,
    }


def _variable_group_for(*, variable_name: str | None, market_family: str | None) -> str | None:
    if variable_name in VARIABLE_GROUP_BY_VARIABLE_NAME:
        return VARIABLE_GROUP_BY_VARIABLE_NAME[variable_name]
    if market_family in {"sea_ice_extent", "global_temperature_index"}:
        return "climate_index"
    return None


def _policy_family_for(*, variable_name: str | None, market_family: str | None) -> str | None:
    if variable_name in POLICY_FAMILY_BY_VARIABLE_NAME:
        return POLICY_FAMILY_BY_VARIABLE_NAME[variable_name]
    return market_family


def _find_precision_policy_ref(
    *,
    bundle: dict[str, Any],
    policy_family: str | None,
    variable_name: str | None,
) -> str | None:
    for policy in bundle["precision_policy_registry"].get("policies") or []:
        if not isinstance(policy, dict):
            continue
        if str(policy.get("family") or "") == str(policy_family or ""):
            return str(policy.get("policy_id") or "") or None
    return None


def _find_rounding_policy_ref(
    *,
    bundle: dict[str, Any],
    policy_family: str | None,
) -> str | None:
    for policy in bundle["rounding_policy_registry"].get("policies") or []:
        if not isinstance(policy, dict):
            continue
        if str(policy.get("family") or "") == str(policy_family or ""):
            return str(policy.get("policy_id") or "") or None
    return None


def _find_band_mapping_policy_ref(
    *,
    bundle: dict[str, Any],
    band_scheme: str | None,
) -> str | None:
    for policy in bundle["band_mapping_policy_registry"].get("policies") or []:
        if not isinstance(policy, dict):
            continue
        if str(policy.get("band_scheme") or "") == str(band_scheme or ""):
            return str(policy.get("policy_id") or "") or None
    return None
