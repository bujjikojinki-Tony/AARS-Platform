from __future__ import annotations

BAND_SCHEME_BY_VARIABLE: dict[str, str] = {
    "daily_max_temperature": "temperature_4_bucket",
    "daily_min_temperature": "temperature_4_bucket",
    "daily_precipitation_sum": "precipitation_range_3way",
    "daily_snowfall_sum": "snowfall_range_3way",
    "daily_max_wind_speed": "wind_speed_range_3way",
}

BAND_SCHEME_BY_FAMILY: dict[str, str] = {
    "station_temperature": "temperature_4_bucket",
    "weather_metric": "weather_metric_unknown",
    "sea_ice_extent": "sea_ice_range_3way",
    "global_temperature_index": "global_temperature_index_ordinal",
}


def resolve_band_scheme(
    *,
    variable_name: str | None,
    market_family: str,
) -> str | None:
    if variable_name and variable_name in BAND_SCHEME_BY_VARIABLE:
        return BAND_SCHEME_BY_VARIABLE[variable_name]
    return BAND_SCHEME_BY_FAMILY.get(market_family)

