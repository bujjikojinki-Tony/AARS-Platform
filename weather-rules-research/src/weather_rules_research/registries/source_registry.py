from __future__ import annotations

FAMILY_REQUIRED_SOURCE: dict[str, str | None] = {
    "station_temperature": "open_meteo_plus_station_mapping",
    "weather_metric": "open_meteo_plus_station_mapping",
    "sea_ice_extent": "nsidc_arctic_sea_ice_extent",
    "global_temperature_index": "global_temperature_index_snapshot",
    "unknown": None,
}

SOURCE_CONTRACT_PROFILES: dict[str, dict] = {
    "station_shanghai_exact": {
        "required_data_source": "wunderground_zspd",
        "required_sources": (
            "wunderground_zspd_history",
            "wunderground_zspd_realtime",
            "forecast_station_mapping",
        ),
        "settlement_source_type": "station_observation",
        "official_vs_proxy_source": "official",
        "source_match_grade": "exact_station",
        "official_source_url": "https://www.wunderground.com/history/weekly/cn/shanghai/ZSPD",
        "source_note": "Shanghai weather markets are pinned to Pudong Airport (ZSPD).",
    },
    "station_fallback": {
        "required_data_source": "open_meteo_plus_station_mapping",
        "required_sources": (
            "forecast_station_mapping",
            "official_station_observation",
        ),
        "settlement_source_type": "station_observation",
        "official_vs_proxy_source": "fallback",
        "source_match_grade": "family_only",
        "official_source_url": None,
        "source_note": (
            "Market family is recognized, but no exact rule-backed station match was found."
        ),
    },
    "station_exact": {
        "required_data_source": "open_meteo_plus_station_mapping",
        "required_sources": (
            "forecast_station_mapping",
            "official_station_observation",
        ),
        "settlement_source_type": "station_observation",
        "official_vs_proxy_source": "official",
        "source_match_grade": "exact_station",
        "official_source_url": None,
        "source_note": "Rulebook station mapping matched the market to a settlement-grade station.",
    },
    "sea_ice_family_exact": {
        "required_data_source": "nsidc_arctic_sea_ice_extent",
        "required_sources": ("nsidc_arctic_sea_ice_extent",),
        "settlement_source_type": "climate_index_snapshot",
        "official_vs_proxy_source": "official",
        "source_match_grade": "family_exact",
        "official_source_url": "https://nsidc.org/arcticseaicenews/",
        "source_note": "Sea ice extent markets use an NSIDC-style extent snapshot contract.",
    },
    "global_temperature_family_exact": {
        "required_data_source": "global_temperature_index_snapshot",
        "required_sources": ("global_temperature_index_snapshot",),
        "settlement_source_type": "climate_index_rank",
        "official_vs_proxy_source": "proxy",
        "source_match_grade": "family_exact",
        "official_source_url": "https://berkeleyearth.org/data/",
        "source_note": (
            "Global temperature rank markets are matched at the family level. "
            "Exact settlement wording should still be reviewed before live promotion."
        ),
    },
    "unknown_unmatched": {
        "required_data_source": None,
        "required_sources": (),
        "settlement_source_type": "unknown",
        "official_vs_proxy_source": "unknown",
        "source_match_grade": "unmatched",
        "official_source_url": None,
        "source_note": "No stable resolver contract is available for this market family yet.",
    },
}


def required_data_source_for_family(market_family: str) -> str | None:
    return FAMILY_REQUIRED_SOURCE.get(market_family)


def get_source_contract_profile(profile_name: str) -> dict:
    return SOURCE_CONTRACT_PROFILES.get(profile_name, SOURCE_CONTRACT_PROFILES["unknown_unmatched"])

