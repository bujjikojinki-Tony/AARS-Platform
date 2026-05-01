from __future__ import annotations

from backend.models.weather import FreshnessStatus
from backend.models.weather import WeatherMetric
from backend.weather.market_question_parser import MarketQuestionParser
from backend.weather.noaa_source import NoaaPlaceholderSource
from backend.weather.open_meteo_source import OpenMeteoSource
from backend.weather.source_health_checker import SourceHealthChecker
from backend.weather.weather_market_resolver import WeatherMarketResolver
from backend.weather.weather_source_registry import WeatherSourceRegistry


def test_weather_source_registry_selects_open_meteo_for_tokyo() -> None:
    parser = MarketQuestionParser(default_year=2026)
    descriptor = parser.parse(
        "mock_weather_strong_yes",
        "Will Tokyo high temperature exceed 30C on June 1?",
    )
    descriptor = WeatherMarketResolver().resolve(descriptor)
    registry = WeatherSourceRegistry(
        sources=[OpenMeteoSource(allow_network=False), NoaaPlaceholderSource()]
    )

    sources = registry.select_sources(descriptor)

    assert len(sources) == 1
    assert sources[0].source_name == "open_meteo"


def test_weather_source_registry_selects_open_meteo_and_noaa_for_new_york() -> None:
    parser = MarketQuestionParser(default_year=2026)
    descriptor = parser.parse(
        "mock_weather_ny",
        "Will max temperature in New York exceed 30C on June 1?",
    )
    descriptor.metric = WeatherMetric.DAILY_HIGH
    descriptor = WeatherMarketResolver().resolve(descriptor)
    registry = WeatherSourceRegistry(
        sources=[OpenMeteoSource(allow_network=False), NoaaPlaceholderSource()]
    )

    sources = registry.select_sources(descriptor)
    names = [source.source_name for source in sources]

    assert "open_meteo" in names
    assert "noaa_placeholder" in names


def test_source_health_checker_marks_missing_when_no_value() -> None:
    parser = MarketQuestionParser(default_year=2026)
    descriptor = parser.parse(
        "mock_weather_tokyo",
        "Will Tokyo high temperature exceed 30C on June 1?",
    )
    descriptor = WeatherMarketResolver().resolve(descriptor)
    record = OpenMeteoSource(allow_network=False).fetch(descriptor)
    record.normalized_value = None

    checked = SourceHealthChecker().check(record)

    assert checked.freshness_status == FreshnessStatus.MISSING
