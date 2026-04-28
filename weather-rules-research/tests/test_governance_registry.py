from __future__ import annotations

from pathlib import Path

from weather_rules_research.governance import (
    get_band_mapping_policy,
    get_band_mapping_policy_for_scheme,
    get_canonical_value,
    get_display_value,
    get_precision_policy,
    get_precision_policy_for_family,
    get_rounding_policy,
    get_rounding_policy_for_family,
    get_source_policy_definition,
    get_unit_policy,
    get_unit_policy_for_family,
    load_measurement_registry_bundle,
    load_source_policy_registry,
    normalize_measurement,
    validate_registry_bundle,
)


def test_governance_registries_load_and_validate() -> None:
    source_registry = load_source_policy_registry()
    measurement_bundle = load_measurement_registry_bundle()

    errors = validate_registry_bundle(
        source_registry=source_registry,
        measurement_bundle=measurement_bundle,
    )

    assert errors == []
    assert source_registry["schema_version"] == "source_policy_registry.v1"
    assert get_source_policy_definition("polymarket_clob")["priority_level"] == "critical"
    assert get_unit_policy("temperature")["canonical_unit"] == "celsius"
    assert get_unit_policy_for_family("temperature_daily_max")["canonical_unit"] == "celsius"
    assert get_precision_policy("precision_policy.temperature_daily_max.v1")["band_precision"] == "integer"
    assert get_precision_policy_for_family("temperature_daily_max")["comparison_precision"] == 2
    assert get_rounding_policy("rounding_policy.weather_metric.precipitation.v1")["version"] == "v1"
    assert get_rounding_policy_for_family("weather_metric.precipitation")["family"] == "weather_metric.precipitation"
    assert get_band_mapping_policy("band_mapping.precipitation_mm_threshold.v1")["canonical_unit"] == "mm"
    assert get_band_mapping_policy("band_mapping.temperature_celsius_integer.v1")["band_scheme"] == "temperature_4_bucket"
    assert get_band_mapping_policy_for_scheme("temperature_4_bucket")["policy_id"] == "band_mapping.temperature_celsius_integer.v1"
    assert get_canonical_value({"raw_value": 32, "raw_unit": "fahrenheit"}, family="temperature_daily_max") == 0.0
    assert get_display_value({"raw_value": 29.44, "raw_unit": "celsius"}, family="temperature_daily_max") == 29.4
    assert normalize_measurement({"value": 29.44, "unit": "celsius"}, family="temperature_daily_max")[
        "normalization_version"
    ] == "measurement_normalization.v1"


def test_source_registry_validator_reports_missing_required_fields(tmp_path: Path) -> None:
    broken_registry = tmp_path / "source_policy_registry.json"
    broken_registry.write_text(
        '{"schema_version":"source_policy_registry.v1","sources":[{"source_name":"broken"}]}',
        encoding="utf-8",
    )

    source_registry = load_source_policy_registry(broken_registry)
    errors = validate_registry_bundle(
        source_registry=source_registry,
        measurement_bundle=load_measurement_registry_bundle(),
    )

    assert any("missing required fields" in error for error in errors)
