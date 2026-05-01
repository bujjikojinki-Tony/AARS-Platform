from __future__ import annotations

from backend.models.weather import EvidenceConflictLevel
from backend.models.weather import EvidenceFreshness
from backend.models.weather import WeatherDirection
from backend.weather.evidence_pack_builder import EvidencePackBuilder
from backend.weather.market_question_parser import MarketQuestionParser
from backend.weather.noaa_source import NoaaPlaceholderSource
from backend.weather.open_meteo_source import OpenMeteoSource
from backend.weather.source_health_checker import SourceHealthChecker
from backend.weather.weather_market_resolver import WeatherMarketResolver
from backend.weather.weather_source_registry import WeatherSourceRegistry
from backend.weather.weather_view_builder import WeatherViewBuilder


def test_evidence_pack_and_weather_view_for_tokyo() -> None:
    parser = MarketQuestionParser(default_year=2026)
    resolver = WeatherMarketResolver()
    descriptor = parser.parse(
        "mock_weather_strong_yes",
        "Will Tokyo high temperature exceed 30C on June 1?",
    )
    descriptor = resolver.resolve(descriptor)
    registry = WeatherSourceRegistry(
        sources=[OpenMeteoSource(allow_network=False), NoaaPlaceholderSource()]
    )
    checker = SourceHealthChecker()

    records = []
    for source in registry.select_sources(descriptor):
        records.append(checker.check(source.fetch(descriptor)))

    pack = EvidencePackBuilder().build(descriptor, records)
    view = WeatherViewBuilder(default_sigma=2.5).build(pack)

    assert pack.evidence_freshness == EvidenceFreshness.FRESH
    assert pack.evidence_conflict_level == EvidenceConflictLevel.NONE
    assert any(source.source_name == "open_meteo_mock" for source in pack.sources)
    assert round(view.expected_value, 1) == 31.2
    assert round(view.expected_range_low, 1) == 28.7
    assert round(view.expected_range_high, 1) == 33.7
    assert view.sigma == 2.5
    assert view.threshold == 30
    assert view.direction == WeatherDirection.ABOVE
