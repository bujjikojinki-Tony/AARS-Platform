from weather_rules_research.models.market_rule import MarketRule
from weather_rules_research.rules.market_taxonomy import classify_market_question
from weather_rules_research.rules.resolver_contract_registry import ResolverContractRegistry


def test_station_contract_is_exact_for_central_park_rule():
    registry = ResolverContractRegistry()
    rule = MarketRule(
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
        source_name="official_source",
        raw_rules_text="Official station observation from Central Park.",
        parse_confidence=0.92,
        needs_review=False,
    )

    contract = registry.build_contract(
        taxonomy=classify_market_question(rule.market_question),
        market_snapshot={"market_id": "sample_market_001", "location_name": "Central Park"},
        rule=rule,
    )

    assert contract.source_match_grade == "exact_station"
    assert contract.official_vs_proxy_source == "official"
    assert contract.settlement_source_type == "station_observation"
    assert contract.official_source_url == "https://api.weather.gov/stations/KNYC"
    assert contract.station_id == "KNYC"
    assert contract.source_policy_ref == "wunderground_station"
    assert contract.unit_policy_ref == "temperature"
    assert contract.precision_policy_ref == "precision_policy.temperature_daily_max.v1"
    assert contract.rounding_policy_ref == "rounding_policy.temperature_daily_max.v1"
    assert contract.band_mapping_policy_ref == "band_mapping.temperature_celsius_integer.v1"


def test_station_contract_uses_shanghai_override():
    registry = ResolverContractRegistry()
    rule = MarketRule(
        market_id="379803",
        market_question="Highest temperature in Shanghai on April 16?",
        market_type="daily_high_temperature",
        location_name="Shanghai",
        target_date="April 16",
        station_name="Shanghai Pudong International Airport",
        nws_station_id=None,
        cdo_station_id=None,
        variable_name="daily_max_temperature",
        timezone="Asia/Shanghai",
        source_name="official_source",
        raw_rules_text="Official Shanghai Pudong airport observation.",
        parse_confidence=0.93,
        needs_review=False,
    )

    contract = registry.build_contract(
        taxonomy=classify_market_question(rule.market_question),
        market_snapshot={"market_id": "379803", "location_name": "Shanghai"},
        rule=rule,
    )

    assert contract.required_data_source == "wunderground_zspd"
    assert contract.source_match_grade == "exact_station"
    assert contract.official_vs_proxy_source == "official"
    assert contract.station_id == "ZSPD"
    assert contract.official_source_url == "https://www.wunderground.com/history/weekly/cn/shanghai/ZSPD"
    assert contract.source_policy_ref == "wunderground_station"
    assert contract.unit_policy_ref == "temperature"
    assert contract.precision_policy_ref == "precision_policy.temperature_daily_max.v1"
    assert contract.band_mapping_policy_ref == "band_mapping.temperature_celsius_integer.v1"


def test_global_temperature_contract_is_family_level_proxy():
    registry = ResolverContractRegistry()
    taxonomy = classify_market_question("Will 2026 be the third-hottest year on record?")

    contract = registry.build_contract(
        taxonomy=taxonomy,
        market_snapshot={"market_id": "678686"},
        rule=None,
        resolution_snapshot={"expected_band": "top_3"},
    )

    assert contract.required_data_source == "global_temperature_index_snapshot"
    assert contract.source_match_grade == "family_exact"
    assert contract.official_vs_proxy_source == "proxy"
    assert contract.settlement_source_type == "climate_index_rank"
    assert contract.source_policy_ref == "climate_index_source"
    assert contract.unit_policy_ref == "climate_index"
    assert contract.precision_policy_ref == "precision_policy.global_temperature_index.v1"
    assert contract.rounding_policy_ref == "rounding_policy.global_temperature_index.v1"
    assert contract.band_mapping_policy_ref == "band_mapping.global_temperature_index_ordinal.v1"
