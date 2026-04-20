SOURCE_REGISTRY: dict[str, dict] = {
    "metar": {
        "source_type": "observation",
        "official_or_proxy": "proxy",
        "freshness_expectation_minutes": 90,
        "timeout_seconds": 15,
        "cache_policy": "cache_first",
        "applicable_market_families": ["temperature_daily_max", "temperature_daily_min"],
    },
    "official_obs": {
        "source_type": "observation",
        "official_or_proxy": "official",
        "freshness_expectation_minutes": 1440,
        "timeout_seconds": 30,
        "cache_policy": "cache_first",
        "applicable_market_families": [
            "temperature_daily_max",
            "temperature_daily_min",
            "precipitation_amount",
            "snowfall_amount",
            "wind_speed_max",
        ],
    },
}

