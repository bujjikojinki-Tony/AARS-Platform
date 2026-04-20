from pathlib import Path

from weather_rules_research.rules.live_market_resolver import load_rulebook, resolve_rule_for_market


def test_resolve_rule_for_matching_temperature_market():
    rules = load_rulebook(
        Path(__file__).resolve().parents[1] / "data" / "outputs" / "sample_rulebook.json"
    )
    market_snapshot = {
        "market_id": "sample_market_001",
        "market_question": "Highest temperature in Central Park on Apr 12?",
        "location_name": "Central Park",
    }

    rule, reason, taxonomy = resolve_rule_for_market(market_snapshot, rules)

    assert rule is not None
    assert rule.market_id == "sample_market_001"
    assert reason in {"matched_by_market_id", "matched_by_question_and_location"}
    assert taxonomy.supported_by_current_pipeline is True
    assert taxonomy.market_family == "station_temperature"
    assert taxonomy.band_scheme == "temperature_4_bucket"


def test_resolve_rule_for_unmatched_live_market():
    rules = load_rulebook(
        Path(__file__).resolve().parents[1] / "data" / "outputs" / "sample_rulebook.json"
    )
    market_snapshot = {
        "market_id": "693874",
        "market_question": "Will the minimum Arctic sea ice extent this summer be between 4.8m & 5m square kilometers?",
        "location_name": "UNKNOWN",
    }

    rule, reason, taxonomy = resolve_rule_for_market(market_snapshot, rules)

    assert rule is None
    assert reason == "sea_ice_extent_snapshot_expected"
    assert taxonomy.supported_by_current_pipeline is True
    assert taxonomy.market_family == "sea_ice_extent"
    assert taxonomy.band_scheme == "sea_ice_range_3way"


def test_resolve_rule_for_shanghai_temperature_market():
    rules = load_rulebook(
        Path(__file__).resolve().parents[1] / "data" / "outputs" / "sample_rulebook.json"
    )
    market_snapshot = {
        "market_id": "sample_market_shanghai_001",
        "market_question": "Highest temperature in Shanghai on Apr 14?",
        "location_name": "Shanghai",
    }

    rule, reason, taxonomy = resolve_rule_for_market(market_snapshot, rules)

    assert rule is not None
    assert rule.market_id == "sample_market_shanghai_001"
    assert rule.station_name == "Shanghai Pudong International Airport"
    assert reason in {"matched_by_market_id", "matched_by_question_and_location"}
    assert taxonomy.supported_by_current_pipeline is True
    assert taxonomy.market_family == "station_temperature"
    assert taxonomy.band_scheme == "temperature_4_bucket"
