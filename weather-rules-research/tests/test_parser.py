from weather_rules_research.rules import normalize_market_rule, parse_market_question, parse_rules_text


def test_parse_market_question_extracts_high_temperature_fields() -> None:
    parsed = parse_market_question("Highest temperature in Central Park on Apr 12?")

    assert parsed.location_name == "Central Park"
    assert parsed.market_type == "daily_high_temperature"
    assert parsed.target_date_raw == "Apr 12"
    assert parsed.variable_name == "daily_max_temperature"
    assert parsed.parse_confidence >= 0.9
    assert parsed.needs_review is False


def test_parse_market_question_supports_low_temperature() -> None:
    parsed = parse_market_question("Lowest temperature in Singapore on March 15?")

    assert parsed.location_name == "Singapore"
    assert parsed.market_type == "daily_low_temperature"
    assert parsed.variable_name == "daily_min_temperature"


def test_parse_market_question_supports_global_temperature_index() -> None:
    parsed = parse_market_question("Will 2026 be the third-hottest year on record?")

    assert parsed.market_type == "global_temperature_index_ordinal"
    assert parsed.variable_name == "global_temperature_index"
    assert parsed.parse_confidence >= 0.8
    assert parsed.needs_review is False


def test_parse_market_question_supports_precipitation() -> None:
    parsed = parse_market_question("Rainfall in Shanghai on Apr 18?")

    assert parsed.location_name == "Shanghai"
    assert parsed.market_type == "daily_precipitation"
    assert parsed.variable_name == "daily_precipitation_sum"
    assert parsed.parse_confidence >= 0.85
    assert parsed.needs_review is False


def test_parse_market_question_supports_precipitation_with_range() -> None:
    parsed = parse_market_question("Will rainfall in Shanghai on Apr 18 be between 10mm and 20mm?")

    assert parsed.location_name == "Shanghai"
    assert parsed.target_date_raw == "Apr 18"
    assert parsed.variable_name == "daily_precipitation_sum"


def test_parse_market_question_supports_snowfall_with_range() -> None:
    parsed = parse_market_question("Will snowfall in Shanghai on Apr 18 be above 5cm?")

    assert parsed.location_name == "Shanghai"
    assert parsed.target_date_raw == "Apr 18"
    assert parsed.variable_name == "daily_snowfall_sum"


def test_parse_market_question_supports_wind_speed() -> None:
    parsed = parse_market_question("Will wind speed in Shanghai on Apr 18 be between 20 km/h and 40 km/h?")

    assert parsed.location_name == "Shanghai"
    assert parsed.target_date_raw == "Apr 18"
    assert parsed.variable_name == "daily_max_wind_speed"


def test_parse_rules_text_detects_low_temperature_metric() -> None:
    parsed = parse_rules_text(
        "This market resolves using official station data from Changi Airport in Singapore time for the daily low from NOAA."
    )

    assert parsed.station_id == "WSSS"
    assert parsed.timezone == "Asia/Singapore"
    assert parsed.variable_name == "daily_min_temperature"
    assert "official_source" in parsed.extracted_flags
    assert parsed.needs_review is False


def test_parse_rules_text_detects_shanghai_station() -> None:
    parsed = parse_rules_text(
        "Resolves based on the official highest temperature recorded at Shanghai Pudong International Airport station in Shanghai time."
    )

    assert parsed.station_name == "Shanghai Pudong International Airport"
    assert parsed.timezone == "Asia/Shanghai"
    assert parsed.variable_name == "daily_max_temperature"
    assert "station_shanghai_pudong" in parsed.extracted_flags


def test_parse_rules_text_detects_precipitation_metric() -> None:
    parsed = parse_rules_text(
        "Resolves using official station rainfall data from Shanghai Pudong International Airport in Shanghai time."
    )

    assert parsed.station_name == "Shanghai Pudong International Airport"
    assert parsed.variable_name == "daily_precipitation_sum"
    assert "variable_daily_precipitation_sum" in parsed.extracted_flags


def test_parse_rules_text_detects_snowfall_metric() -> None:
    parsed = parse_rules_text(
        "Resolves using official station snowfall data from Shanghai Pudong International Airport in Shanghai time."
    )

    assert parsed.station_name == "Shanghai Pudong International Airport"
    assert parsed.variable_name == "daily_snowfall_sum"
    assert "variable_daily_snowfall_sum" in parsed.extracted_flags


def test_parse_rules_text_detects_wind_metric() -> None:
    parsed = parse_rules_text(
        "Resolves using official maximum wind speed data from Shanghai Pudong International Airport in Shanghai time."
    )

    assert parsed.station_name == "Shanghai Pudong International Airport"
    assert parsed.variable_name == "daily_max_wind_speed"
    assert "variable_daily_max_wind_speed" in parsed.extracted_flags


def test_normalize_market_rule_marks_low_confidence_input_for_review() -> None:
    rule = normalize_market_rule(
        market_id="market-3",
        question="Temperature in Phoenix tomorrow?",
        rules_text=None,
    )

    assert rule.parse_confidence == 0.2
    assert rule.market_type == "unknown"
    assert rule.location_name == "UNKNOWN"
    assert rule.needs_review is True
