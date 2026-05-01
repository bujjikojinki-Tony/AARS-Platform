from backend.weather.evidence_pack_builder import EvidencePackBuilder
from backend.weather.market_question_parser import MarketQuestionParser
from backend.weather.noaa_source import NoaaPlaceholderSource
from backend.weather.open_meteo_source import OpenMeteoSource
from backend.weather.source_health_checker import SourceHealthChecker
from backend.weather.weather_market_resolver import WeatherMarketResolver
from backend.weather.weather_source_registry import WeatherSourceRegistry
from backend.weather.weather_view_builder import WeatherViewBuilder


parser = MarketQuestionParser(default_year=2026)
resolver = WeatherMarketResolver()
descriptor = parser.parse(
    "mock_weather_strong_yes",
    "Will Tokyo high temperature exceed 30C on June 1?",
)
descriptor = resolver.resolve(descriptor)
registry = WeatherSourceRegistry(
    sources=[
        OpenMeteoSource(allow_network=False),
        NoaaPlaceholderSource(),
    ]
)
checker = SourceHealthChecker()
records = []
for source in registry.select_sources(descriptor):
    record = source.fetch(descriptor)
    records.append(checker.check(record))
pack = EvidencePackBuilder().build(descriptor, records)
view = WeatherViewBuilder(default_sigma=2.5).build(pack)

print("EvidencePack:")
print(pack.model_dump())
print("\nWeatherView:")
print(view.model_dump())
