from weather_rules_research.open_meteo.extractors import OpenMeteoExtractor


def test_extract_daily_max_from_daily_payload() -> None:
    extractor = OpenMeteoExtractor()

    payload = {
        "daily": {
            "time": ["2026-04-11", "2026-04-12", "2026-04-13"],
            "temperature_2m_max": [25.1, 27.8, 26.4],
        }
    }

    result = extractor.extract_for_market_rule(
        payload=payload,
        target_date="2026-04-12",
        variable_name="daily_max_temperature",
    )

    assert result.value == 27.8
    assert result.source_mode == "Daily forecast matched"
    assert result.source_path == "daily.temperature_2m_max"


def test_extract_daily_max_from_hourly_fallback() -> None:
    extractor = OpenMeteoExtractor()

    payload = {
        "hourly": {
            "time": [
                "2026-04-12T00:00",
                "2026-04-12T06:00",
                "2026-04-12T12:00",
                "2026-04-12T18:00",
            ],
            "temperature_2m": [21.0, 24.5, 28.2, 26.1],
        }
    }

    result = extractor.extract_for_market_rule(
        payload=payload,
        target_date="2026-04-12",
        variable_name="daily_max_temperature",
    )

    assert result.value == 28.2
    assert result.source_mode == "Hourly fallback used"
    assert result.source_path == "hourly.temperature_2m:max"


def test_extract_daily_min_from_hourly_fallback() -> None:
    extractor = OpenMeteoExtractor()

    payload = {
        "hourly": {
            "time": [
                "2026-04-12T00:00",
                "2026-04-12T06:00",
                "2026-04-12T12:00",
                "2026-04-12T18:00",
            ],
            "temperature_2m": [20.4, 19.1, 28.2, 24.7],
        }
    }

    result = extractor.extract_for_market_rule(
        payload=payload,
        target_date="2026-04-12",
        variable_name="daily_min_temperature",
    )

    assert result.value == 19.1
    assert result.source_mode == "Hourly fallback used"
    assert result.source_path == "hourly.temperature_2m:min"


def test_extract_daily_precipitation_from_daily_payload() -> None:
    extractor = OpenMeteoExtractor()

    payload = {
        "daily": {
            "time": ["2026-04-11", "2026-04-12"],
            "precipitation_sum": [2.5, 8.7],
        }
    }

    result = extractor.extract_for_market_rule(
        payload=payload,
        target_date="2026-04-12",
        variable_name="daily_precipitation_sum",
    )

    assert result.value == 8.7
    assert result.source_mode == "Daily forecast matched"
    assert result.source_path == "daily.precipitation_sum"


def test_extract_daily_precipitation_from_hourly_fallback() -> None:
    extractor = OpenMeteoExtractor()

    payload = {
        "hourly": {
            "time": [
                "2026-04-12T00:00",
                "2026-04-12T06:00",
                "2026-04-12T12:00",
                "2026-04-12T18:00",
            ],
            "precipitation": [0.5, 1.0, 2.0, 0.5],
        }
    }

    result = extractor.extract_for_market_rule(
        payload=payload,
        target_date="2026-04-12",
        variable_name="daily_precipitation_sum",
    )

    assert result.value == 4.0
    assert result.source_mode == "Hourly fallback used"
    assert result.source_path == "hourly.precipitation:sum"


def test_extract_daily_snowfall_from_daily_payload() -> None:
    extractor = OpenMeteoExtractor()

    payload = {
        "daily": {
            "time": ["2026-04-11", "2026-04-12"],
            "snowfall_sum": [1.5, 6.2],
        }
    }

    result = extractor.extract_for_market_rule(
        payload=payload,
        target_date="2026-04-12",
        variable_name="daily_snowfall_sum",
    )

    assert result.value == 6.2
    assert result.source_mode == "Daily forecast matched"
    assert result.source_path == "daily.snowfall_sum"


def test_extract_daily_max_wind_speed_from_hourly_fallback() -> None:
    extractor = OpenMeteoExtractor()

    payload = {
        "hourly": {
            "time": [
                "2026-04-12T00:00",
                "2026-04-12T06:00",
                "2026-04-12T12:00",
                "2026-04-12T18:00",
            ],
            "wind_speed_10m": [18.0, 26.0, 34.5, 28.0],
        }
    }

    result = extractor.extract_for_market_rule(
        payload=payload,
        target_date="2026-04-12",
        variable_name="daily_max_wind_speed",
    )

    assert result.value == 34.5
    assert result.source_mode == "Hourly fallback used"
    assert result.source_path == "hourly.wind_speed_10m:max"
