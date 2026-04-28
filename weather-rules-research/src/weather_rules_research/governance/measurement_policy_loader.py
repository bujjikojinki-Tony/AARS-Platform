from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from weather_rules_research.settings import (
    BAND_MAPPING_POLICY_REGISTRY_JSON,
    MEASUREMENT_REGISTRY_DIR,
    PRECISION_POLICY_REGISTRY_JSON,
    ROUNDING_POLICY_REGISTRY_JSON,
    UNIT_REGISTRY_JSON,
)

UNIT_REGISTRY_SCHEMA_VERSION = "unit_registry.v1"
PRECISION_POLICY_REGISTRY_SCHEMA_VERSION = "precision_policy_registry.v1"
ROUNDING_POLICY_REGISTRY_SCHEMA_VERSION = "rounding_policy_registry.v1"
BAND_MAPPING_POLICY_REGISTRY_SCHEMA_VERSION = "band_mapping_policy_registry.v1"


def _load_json_file(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(default)
    if not isinstance(payload, dict):
        return dict(default)
    return payload


def _default_unit_registry() -> dict[str, Any]:
    return {"schema_version": UNIT_REGISTRY_SCHEMA_VERSION, "generated_at": None, "variable_groups": []}


def _default_precision_registry() -> dict[str, Any]:
    return {
        "schema_version": PRECISION_POLICY_REGISTRY_SCHEMA_VERSION,
        "generated_at": None,
        "policies": [],
    }


def _default_rounding_registry() -> dict[str, Any]:
    return {
        "schema_version": ROUNDING_POLICY_REGISTRY_SCHEMA_VERSION,
        "generated_at": None,
        "policies": [],
    }


def _default_band_mapping_registry() -> dict[str, Any]:
    return {
        "schema_version": BAND_MAPPING_POLICY_REGISTRY_SCHEMA_VERSION,
        "generated_at": None,
        "policies": [],
    }


@lru_cache(maxsize=4)
def load_measurement_registry_bundle(base_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(base_dir or MEASUREMENT_REGISTRY_DIR)
    unit_registry = _load_json_file(root / UNIT_REGISTRY_JSON.name, _default_unit_registry())
    precision_registry = _load_json_file(
        root / PRECISION_POLICY_REGISTRY_JSON.name,
        _default_precision_registry(),
    )
    rounding_registry = _load_json_file(
        root / ROUNDING_POLICY_REGISTRY_JSON.name,
        _default_rounding_registry(),
    )
    band_mapping_registry = _load_json_file(
        root / BAND_MAPPING_POLICY_REGISTRY_JSON.name,
        _default_band_mapping_registry(),
    )

    unit_registry.setdefault("schema_version", UNIT_REGISTRY_SCHEMA_VERSION)
    precision_registry.setdefault("schema_version", PRECISION_POLICY_REGISTRY_SCHEMA_VERSION)
    rounding_registry.setdefault("schema_version", ROUNDING_POLICY_REGISTRY_SCHEMA_VERSION)
    band_mapping_registry.setdefault("schema_version", BAND_MAPPING_POLICY_REGISTRY_SCHEMA_VERSION)

    if not isinstance(unit_registry.get("variable_groups"), list):
        unit_registry["variable_groups"] = []
    if not isinstance(precision_registry.get("policies"), list):
        precision_registry["policies"] = []
    if not isinstance(rounding_registry.get("policies"), list):
        rounding_registry["policies"] = []
    if not isinstance(band_mapping_registry.get("policies"), list):
        band_mapping_registry["policies"] = []

    return {
        "schema_version": "measurement_registry_bundle.v1",
        "base_dir": str(root),
        "unit_registry": unit_registry,
        "precision_policy_registry": precision_registry,
        "rounding_policy_registry": rounding_registry,
        "band_mapping_policy_registry": band_mapping_registry,
    }


def get_unit_policy(
    variable_group: str,
    *,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    bundle = load_measurement_registry_bundle(base_dir)
    for policy in bundle["unit_registry"].get("variable_groups") or []:
        if isinstance(policy, dict) and str(policy.get("variable_group") or "") == str(variable_group):
            return policy
    return {}


def get_precision_policy(
    policy_id: str,
    *,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    bundle = load_measurement_registry_bundle(base_dir)
    for policy in bundle["precision_policy_registry"].get("policies") or []:
        if isinstance(policy, dict) and str(policy.get("policy_id") or "") == str(policy_id):
            return policy
    return {}


def get_rounding_policy(
    policy_id: str,
    *,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    bundle = load_measurement_registry_bundle(base_dir)
    for policy in bundle["rounding_policy_registry"].get("policies") or []:
        if isinstance(policy, dict) and str(policy.get("policy_id") or "") == str(policy_id):
            return policy
    return {}


def get_band_mapping_policy(
    policy_id: str,
    *,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    bundle = load_measurement_registry_bundle(base_dir)
    for policy in bundle["band_mapping_policy_registry"].get("policies") or []:
        if isinstance(policy, dict) and str(policy.get("policy_id") or "") == str(policy_id):
            return policy
    return {}


def get_unit_policy_for_family(
    family: str,
    *,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    return get_unit_policy(_family_to_variable_group(family), base_dir=base_dir)


def get_precision_policy_for_family(
    family: str,
    *,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    policy_id = _family_to_precision_policy_id(family)
    if not policy_id:
        return {}
    return get_precision_policy(policy_id, base_dir=base_dir)


def get_rounding_policy_for_family(
    family: str,
    *,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    policy_id = _family_to_rounding_policy_id(family)
    if not policy_id:
        return {}
    return get_rounding_policy(policy_id, base_dir=base_dir)


def get_band_mapping_policy_for_scheme(
    band_scheme: str,
    *,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    policy_id = _band_scheme_to_policy_id(band_scheme)
    if not policy_id:
        return {}
    return get_band_mapping_policy(policy_id, base_dir=base_dir)


def _family_to_variable_group(family: str) -> str:
    normalized = str(family or "").strip().lower()
    if normalized in {"temperature_daily_max", "temperature_daily_min"}:
        return "temperature"
    if "wind_speed" in normalized:
        return "wind_speed"
    if "precipitation" in normalized:
        return "precipitation"
    if "snowfall" in normalized:
        return "snowfall"
    return "climate_index"


def _family_to_precision_policy_id(family: str) -> str:
    normalized = str(family or "").strip().lower()
    if normalized:
        return f"precision_policy.{normalized}.v1"
    return ""


def _family_to_rounding_policy_id(family: str) -> str:
    normalized = str(family or "").strip().lower()
    if normalized:
        return f"rounding_policy.{normalized}.v1"
    return ""


def _band_scheme_to_policy_id(band_scheme: str) -> str:
    normalized = str(band_scheme or "").strip().lower()
    mapping = {
        "temperature_4_bucket": "band_mapping.temperature_celsius_integer.v1",
        "wind_speed_range_3way": "band_mapping.wind_speed_threshold_knots.v1",
        "precipitation_range_3way": "band_mapping.precipitation_mm_threshold.v1",
        "snowfall_range_3way": "band_mapping.snowfall_mm_threshold.v1",
        "global_temperature_index_ordinal": "band_mapping.global_temperature_index_ordinal.v1",
        "sea_ice_range_3way": "band_mapping.sea_ice_range_3way.v1",
    }
    return mapping.get(normalized, "")
