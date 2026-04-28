from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from weather_rules_research.governance.measurement_policy_loader import (
    BAND_MAPPING_POLICY_REGISTRY_SCHEMA_VERSION,
    PRECISION_POLICY_REGISTRY_SCHEMA_VERSION,
    ROUNDING_POLICY_REGISTRY_SCHEMA_VERSION,
    UNIT_REGISTRY_SCHEMA_VERSION,
)
from weather_rules_research.governance.source_policy_loader import SOURCE_POLICY_REGISTRY_SCHEMA_VERSION

SOURCE_POLICY_REQUIRED_FIELDS = {
    "source_name",
    "source_type",
    "primary_use",
    "trigger_mode",
    "write_interval",
    "fresh_threshold",
    "stale_threshold",
    "priority_level",
    "fallback_policy",
    "status",
    "version",
}

UNIT_GROUP_REQUIRED_FIELDS = {
    "variable_group",
    "raw_units",
    "canonical_unit",
    "display_unit",
    "conversion_rules",
}

PRECISION_POLICY_REQUIRED_FIELDS = {
    "policy_id",
    "family",
    "variable_name",
    "canonical_unit",
    "storage_precision",
    "comparison_precision",
    "display_precision",
    "band_precision",
    "status",
    "version",
}

ROUNDING_POLICY_REQUIRED_FIELDS = {"policy_id", "family", "rules", "status", "version"}
BAND_MAPPING_POLICY_REQUIRED_FIELDS = {
    "policy_id",
    "band_scheme",
    "canonical_unit",
    "band_precision",
    "rounding_rule",
    "mapping_formula",
    "status",
    "version",
}


def validate_source_policy_registry(registry: Mapping[str, Any] | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(registry, Mapping):
        return ["source_policy_registry: registry payload must be a mapping"]
    if str(registry.get("schema_version") or "") != SOURCE_POLICY_REGISTRY_SCHEMA_VERSION:
        errors.append(
            "source_policy_registry: schema_version must be "
            f"{SOURCE_POLICY_REGISTRY_SCHEMA_VERSION}"
        )
    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("source_policy_registry: sources must be a non-empty list")
        return errors

    seen: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, Mapping):
            errors.append(f"source_policy_registry.sources[{index}]: entry must be a mapping")
            continue
        missing = sorted(field for field in SOURCE_POLICY_REQUIRED_FIELDS if field not in source)
        if missing:
            errors.append(
                f"source_policy_registry.sources[{index}]: missing required fields {missing}"
            )
        source_name = str(source.get("source_name") or "").strip()
        if not source_name:
            errors.append(f"source_policy_registry.sources[{index}]: source_name must be set")
        elif source_name in seen:
            errors.append(f"source_policy_registry.sources[{index}]: duplicate source_name {source_name}")
        else:
            seen.add(source_name)
    return errors


def validate_measurement_registry_bundle(bundle: Mapping[str, Any] | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(bundle, Mapping):
        return ["measurement_registry_bundle: bundle payload must be a mapping"]
    errors.extend(
        _validate_single_registry(
            bundle.get("unit_registry"),
            schema_version=UNIT_REGISTRY_SCHEMA_VERSION,
            required_top_level={"variable_groups"},
            item_key="variable_groups",
            required_item_fields=UNIT_GROUP_REQUIRED_FIELDS,
            registry_name="unit_registry",
        )
    )
    errors.extend(
        _validate_single_registry(
            bundle.get("precision_policy_registry"),
            schema_version=PRECISION_POLICY_REGISTRY_SCHEMA_VERSION,
            required_top_level={"policies"},
            item_key="policies",
            required_item_fields=PRECISION_POLICY_REQUIRED_FIELDS,
            registry_name="precision_policy_registry",
        )
    )
    errors.extend(
        _validate_single_registry(
            bundle.get("rounding_policy_registry"),
            schema_version=ROUNDING_POLICY_REGISTRY_SCHEMA_VERSION,
            required_top_level={"policies"},
            item_key="policies",
            required_item_fields=ROUNDING_POLICY_REQUIRED_FIELDS,
            registry_name="rounding_policy_registry",
        )
    )
    errors.extend(
        _validate_single_registry(
            bundle.get("band_mapping_policy_registry"),
            schema_version=BAND_MAPPING_POLICY_REGISTRY_SCHEMA_VERSION,
            required_top_level={"policies"},
            item_key="policies",
            required_item_fields=BAND_MAPPING_POLICY_REQUIRED_FIELDS,
            registry_name="band_mapping_policy_registry",
        )
    )
    return errors


def validate_registry_bundle(
    *,
    source_registry: Mapping[str, Any] | None = None,
    measurement_bundle: Mapping[str, Any] | None = None,
) -> list[str]:
    errors = validate_source_policy_registry(source_registry)
    errors.extend(validate_measurement_registry_bundle(measurement_bundle))
    return errors


def _validate_single_registry(
    registry: Any,
    *,
    schema_version: str,
    required_top_level: set[str],
    item_key: str,
    required_item_fields: set[str],
    registry_name: str,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(registry, Mapping):
        return [f"{registry_name}: registry payload must be a mapping"]
    if str(registry.get("schema_version") or "") != schema_version:
        errors.append(f"{registry_name}: schema_version must be {schema_version}")
    for key in required_top_level:
        if key not in registry:
            errors.append(f"{registry_name}: missing top-level key {key}")
    items = registry.get(item_key)
    if not isinstance(items, list) or not items:
        errors.append(f"{registry_name}: {item_key} must be a non-empty list")
        return errors
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            errors.append(f"{registry_name}.{item_key}[{index}]: entry must be a mapping")
            continue
        missing = sorted(field for field in required_item_fields if field not in item)
        if missing:
            errors.append(f"{registry_name}.{item_key}[{index}]: missing required fields {missing}")
    return errors
