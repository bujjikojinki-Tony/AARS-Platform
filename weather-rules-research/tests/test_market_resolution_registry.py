from weather_rules_research.models.market_rule import MarketRule
from weather_rules_research.rules.market_resolution_registry import MarketResolverRegistry


def test_registry_routes_temperature_market_to_station_resolver():
    registry = MarketResolverRegistry()
    rules = [
        MarketRule(
            market_id="sample_market_001",
            market_question="Highest temperature in Central Park on Apr 12?",
            market_type="daily_high_temperature",
            location_name="Central Park",
            target_date="Apr 12",
            station_name="New York City Central Park",
            nws_station_id="KNYC",
            cdo_station_id="GHCND:USW00094728",
            variable_name="daily_max_temperature",
            timezone="America/New_York",
            source_name="market_rules",
            raw_rules_text="Resolves based on the official highest temperature recorded at the designated station for Central Park in New York on April 12, local time.",
            parse_confidence=0.92,
            needs_review=True,
        )
    ]

    resolution = registry.resolve(
        {
            "market_id": "sample_market_001",
            "market_question": "Highest temperature in Central Park on Apr 12?",
            "location_name": "Central Park",
        },
        rules,
    )

    assert resolution.rule is not None
    assert resolution.taxonomy.market_family == "station_temperature"
    assert resolution.resolver_name == "station_temperature_resolver"
    assert resolution.taxonomy.required_data_source == "open_meteo_plus_station_mapping"
    assert resolution.taxonomy.band_scheme == "temperature_4_bucket"


def test_registry_routes_sea_ice_market_to_snapshot_resolver():
    registry = MarketResolverRegistry()

    resolution = registry.resolve(
        {
            "market_id": "693874",
            "market_question": "Will the minimum Arctic sea ice extent this summer be between 4.8m & 5m square kilometers?",
            "location_name": "UNKNOWN",
        },
        [],
    )

    assert resolution.rule is None
    assert resolution.taxonomy.market_family == "sea_ice_extent"
    assert resolution.reason == "sea_ice_extent_snapshot_expected"
    assert resolution.taxonomy.required_data_source == "nsidc_arctic_sea_ice_extent"
    assert resolution.taxonomy.band_scheme == "sea_ice_range_3way"
    assert resolution.taxonomy.supported_by_current_pipeline is True
    assert resolution.snapshot is not None
    assert resolution.snapshot["question_mode"] == "between"
    assert resolution.snapshot["expected_band"] == "in_range"


def test_registry_routes_global_temperature_index_market_to_unsupported_resolver():
    registry = MarketResolverRegistry()

    resolution = registry.resolve(
        {
            "market_id": "gti_001",
            "market_question": "Will 2026 be the third-hottest year on record?",
            "location_name": "UNKNOWN",
        },
        [],
    )

    assert resolution.rule is None
    assert resolution.taxonomy.market_family == "global_temperature_index"
    assert resolution.reason == "global_temperature_index_snapshot_expected"
    assert resolution.taxonomy.required_data_source == "global_temperature_index_snapshot"
    assert resolution.taxonomy.band_scheme == "global_temperature_index_ordinal"
    assert resolution.snapshot is not None
    assert resolution.snapshot["question_mode"] == "ordinal_hottest_year"
    assert resolution.snapshot["ordinal_rank"] == 3


def test_registry_routes_precipitation_market_to_station_weather_metric_resolver():
    registry = MarketResolverRegistry()
    rules = [
        MarketRule(
            market_id="rain_001",
            market_question="Rainfall in Shanghai on Apr 18?",
            market_type="daily_precipitation",
            location_name="Shanghai",
            target_date="Apr 18",
            station_name="Shanghai Pudong International Airport",
            nws_station_id=None,
            cdo_station_id=None,
            variable_name="daily_precipitation_sum",
            timezone="Asia/Shanghai",
            source_name="market_rules",
            raw_rules_text="Official rainfall total at Shanghai Pudong International Airport in Shanghai time.",
            parse_confidence=0.88,
            needs_review=False,
        )
    ]

    resolution = registry.resolve(
        {
            "market_id": "rain_001",
            "market_question": "Rainfall in Shanghai on Apr 18?",
            "location_name": "Shanghai",
        },
        rules,
    )

    assert resolution.rule is not None
    assert resolution.taxonomy.market_family == "weather_metric"
    assert resolution.taxonomy.supported_by_current_pipeline is True
    assert resolution.resolver_name == "station_weather_metric_resolver"
    assert resolution.snapshot is not None
    assert resolution.snapshot["expected_band"] is None


def test_registry_parses_precipitation_thresholds():
    registry = MarketResolverRegistry()
    rules = [
        MarketRule(
            market_id="rain_002",
            market_question="Will rainfall in Shanghai on Apr 18 be between 10mm and 20mm?",
            market_type="daily_precipitation",
            location_name="Shanghai",
            target_date="Apr 18",
            station_name="Shanghai Pudong International Airport",
            nws_station_id=None,
            cdo_station_id=None,
            variable_name="daily_precipitation_sum",
            timezone="Asia/Shanghai",
            source_name="market_rules",
            raw_rules_text="Official rainfall total at Shanghai Pudong International Airport in Shanghai time.",
            parse_confidence=0.88,
            needs_review=False,
        )
    ]

    resolution = registry.resolve(
        {
            "market_id": "rain_002",
            "market_question": "Will rainfall in Shanghai on Apr 18 be between 10mm and 20mm?",
            "location_name": "Shanghai",
        },
        rules,
    )

    assert resolution.snapshot is not None
    assert resolution.snapshot["threshold_lower"] == 10.0
    assert resolution.snapshot["threshold_upper"] == 20.0
    assert resolution.snapshot["expected_band"] == "in_range"


def test_registry_parses_snowfall_thresholds():
    registry = MarketResolverRegistry()
    rules = [
        MarketRule(
            market_id="snow_001",
            market_question="Will snowfall in Shanghai on Apr 18 be above 5cm?",
            market_type="daily_snowfall",
            location_name="Shanghai",
            target_date="Apr 18",
            station_name="Shanghai Pudong International Airport",
            nws_station_id=None,
            cdo_station_id=None,
            variable_name="daily_snowfall_sum",
            timezone="Asia/Shanghai",
            source_name="market_rules",
            raw_rules_text="Official snowfall total at Shanghai Pudong International Airport in Shanghai time.",
            parse_confidence=0.88,
            needs_review=False,
        )
    ]

    resolution = registry.resolve(
        {
            "market_id": "snow_001",
            "market_question": "Will snowfall in Shanghai on Apr 18 be above 5cm?",
            "location_name": "Shanghai",
        },
        rules,
    )

    assert resolution.snapshot is not None
    assert resolution.taxonomy.band_scheme == "snowfall_range_3way"
    assert resolution.snapshot["threshold_lower"] == 5.0
    assert resolution.snapshot["expected_band"] == "above_range"


def test_registry_parses_wind_thresholds():
    registry = MarketResolverRegistry()
    rules = [
        MarketRule(
            market_id="wind_001",
            market_question="Will wind speed in Shanghai on Apr 18 be between 20 km/h and 40 km/h?",
            market_type="daily_max_wind_speed",
            location_name="Shanghai",
            target_date="Apr 18",
            station_name="Shanghai Pudong International Airport",
            nws_station_id=None,
            cdo_station_id=None,
            variable_name="daily_max_wind_speed",
            timezone="Asia/Shanghai",
            source_name="market_rules",
            raw_rules_text="Official maximum wind speed at Shanghai Pudong International Airport in Shanghai time.",
            parse_confidence=0.88,
            needs_review=False,
        )
    ]

    resolution = registry.resolve(
        {
            "market_id": "wind_001",
            "market_question": "Will wind speed in Shanghai on Apr 18 be between 20 km/h and 40 km/h?",
            "location_name": "Shanghai",
        },
        rules,
    )

    assert resolution.snapshot is not None
    assert resolution.taxonomy.band_scheme == "wind_speed_range_3way"
    assert resolution.snapshot["threshold_lower"] == 20.0
    assert resolution.snapshot["threshold_upper"] == 40.0
    assert resolution.snapshot["expected_band"] == "in_range"
