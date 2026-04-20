from weather_rules_research.registries.band_scheme_registry import resolve_band_scheme
from weather_rules_research.registries.source_registry import (
    get_source_contract_profile,
    required_data_source_for_family,
)
from weather_rules_research.rules.market_taxonomy import classify_market_question


def test_band_scheme_registry_resolves_station_temperature_variable() -> None:
    assert (
        resolve_band_scheme(
            variable_name="daily_max_temperature",
            market_family="station_temperature",
        )
        == "temperature_4_bucket"
    )


def test_source_registry_returns_family_required_data_source() -> None:
    assert required_data_source_for_family("sea_ice_extent") == "nsidc_arctic_sea_ice_extent"


def test_source_contract_profile_contains_station_fallback_keys() -> None:
    profile = get_source_contract_profile("station_fallback")
    assert profile["source_match_grade"] == "family_only"
    assert "forecast_station_mapping" in profile["required_sources"]


def test_taxonomy_uses_registry_defaults() -> None:
    taxonomy = classify_market_question("Will 2026 be the third-hottest year on record?")
    assert taxonomy.required_data_source == "global_temperature_index_snapshot"
    assert taxonomy.band_scheme == "global_temperature_index_ordinal"

