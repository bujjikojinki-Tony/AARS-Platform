from __future__ import annotations

import json

from weather_rules_research.models.market_rule import MarketRule
from weather_rules_research.rules.live_market_resolver import load_rulebook
from weather_rules_research.rules.resolver_report import (
    build_resolved_market_rule,
    build_resolver_report,
    write_resolver_outputs,
)


def test_build_resolved_market_rule_for_shanghai_temperature():
    rules = load_rulebook("data/outputs/sample_rulebook.json")
    resolved = build_resolved_market_rule(
        {
            "market_id": "379803",
            "market_question": "Highest temperature in Shanghai on April 16?",
            "location_name": "Shanghai",
        },
        rules,
    )

    assert resolved.resolver_status == "matched"
    assert resolved.market_family == "station_temperature"
    assert resolved.station_id == "ZSPD"
    assert resolved.required_data_source == "wunderground_zspd"
    assert resolved.required_sources == [
        "wunderground_zspd_history",
        "wunderground_zspd_realtime",
        "forecast_station_mapping",
    ]
    assert resolved.official_vs_proxy_source == "official"
    assert resolved.source_match_grade == "exact_station"
    assert resolved.official_source_url == "https://www.wunderground.com/history/weekly/cn/shanghai/ZSPD"
    assert resolved.variable_name == "daily_max_temperature"


def test_build_resolved_market_rule_for_global_temperature_index():
    rules = load_rulebook("data/outputs/sample_rulebook.json")
    resolved = build_resolved_market_rule(
        {
            "market_id": "678686",
            "market_question": "Will 2026 be the hottest year on record?",
            "location_name": "UNKNOWN",
        },
        rules,
    )

    assert resolved.resolver_status == "matched"
    assert resolved.market_family == "global_temperature_index"
    assert resolved.required_data_source == "global_temperature_index_snapshot"
    assert resolved.required_sources == ["global_temperature_index_snapshot"]
    assert resolved.band_scheme == "global_temperature_index_ordinal"
    assert resolved.official_vs_proxy_source == "proxy"
    assert resolved.source_match_grade == "family_exact"
    assert resolved.expected_band == "top_1"
    assert resolved.failure_reason is None


def test_build_resolved_market_rule_for_sea_ice_extent():
    rules = load_rulebook("data/outputs/sample_rulebook.json")
    resolved = build_resolved_market_rule(
        {
            "market_id": "693869",
            "market_question": (
                "Will the minimum Arctic sea ice extent this summer be less than "
                "4m square kilometers?"
            ),
            "location_name": "UNKNOWN",
        },
        rules,
    )

    assert resolved.resolver_status == "matched"
    assert resolved.market_family == "sea_ice_extent"
    assert resolved.required_data_source == "nsidc_arctic_sea_ice_extent"
    assert resolved.required_sources == ["nsidc_arctic_sea_ice_extent"]
    assert resolved.official_vs_proxy_source == "official"
    assert resolved.source_match_grade == "family_exact"
    assert resolved.threshold_upper == 4.0
    assert resolved.failure_reason is None


def test_write_resolver_outputs(tmp_path):
    rules = load_rulebook("data/outputs/sample_rulebook.json")
    resolved = [
        build_resolved_market_rule(
            {
                "market_id": "379803",
                "market_question": "Highest temperature in Shanghai on April 16?",
                "location_name": "Shanghai",
            },
            rules,
        )
    ]
    report_path = tmp_path / "resolver_report.json"
    output_dir = tmp_path / "rules"

    write_resolver_outputs(
        resolved_rules=resolved,
        output_dir=output_dir,
        report_path=report_path,
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    saved_rule = json.loads((output_dir / "market_rule_379803.json").read_text(encoding="utf-8"))

    assert report["tracked_markets"] == 1
    assert report["matched"] == 1
    assert report["matched_family_counts"]["station_temperature"] == 1
    assert report["source_match_grade_counts"]["exact_station"] == 1
    assert report["source_policy_counts"]["official"] == 1
    assert saved_rule["station_id"] == "ZSPD"


def test_build_resolved_market_rule_for_precipitation_metric():
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

    resolved = build_resolved_market_rule(
        {
            "market_id": "rain_001",
            "market_question": "Rainfall in Shanghai on Apr 18?",
            "location_name": "Shanghai",
        },
        rules,
    )

    assert resolved.resolver_status == "matched"
    assert resolved.market_family == "weather_metric"
    assert resolved.variable_name == "daily_precipitation_sum"
    assert resolved.station_id == "ZSPD"
    assert resolved.source_match_grade == "exact_station"


def test_build_resolved_market_rule_for_precipitation_metric_with_range():
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

    resolved = build_resolved_market_rule(
        {
            "market_id": "rain_002",
            "market_question": "Will rainfall in Shanghai on Apr 18 be between 10mm and 20mm?",
            "location_name": "Shanghai",
        },
        rules,
    )

    assert resolved.band_scheme == "precipitation_range_3way"
    assert resolved.threshold_lower == 10.0
    assert resolved.threshold_upper == 20.0
    assert resolved.expected_band == "in_range"


def test_build_resolved_market_rule_for_snowfall_metric_with_range():
    rules = [
        MarketRule(
            market_id="snow_002",
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

    resolved = build_resolved_market_rule(
        {
            "market_id": "snow_002",
            "market_question": "Will snowfall in Shanghai on Apr 18 be above 5cm?",
            "location_name": "Shanghai",
        },
        rules,
    )

    assert resolved.band_scheme == "snowfall_range_3way"
    assert resolved.threshold_lower == 5.0
    assert resolved.expected_band == "above_range"
    assert resolved.unit == "cm"


def test_build_resolved_market_rule_for_wind_metric_with_range():
    rules = [
        MarketRule(
            market_id="wind_002",
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

    resolved = build_resolved_market_rule(
        {
            "market_id": "wind_002",
            "market_question": "Will wind speed in Shanghai on Apr 18 be between 20 km/h and 40 km/h?",
            "location_name": "Shanghai",
        },
        rules,
    )

    assert resolved.band_scheme == "wind_speed_range_3way"
    assert resolved.threshold_lower == 20.0
    assert resolved.threshold_upper == 40.0
    assert resolved.expected_band == "in_range"
    assert resolved.unit == "km_h"
