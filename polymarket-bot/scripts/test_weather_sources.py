from backend.weather.market_question_parser import MarketQuestionParser
from backend.weather.noaa_source import NoaaPlaceholderSource
from backend.weather.open_meteo_source import OpenMeteoSource
from backend.weather.source_health_checker import SourceHealthChecker
from backend.weather.weather_market_resolver import WeatherMarketResolver
from backend.weather.weather_source_registry import WeatherSourceRegistry


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
sources = registry.select_sources(descriptor)
records = []
for source in sources:
    record = source.fetch(descriptor)
    record = checker.check(record)
    records.append(record)

print("descriptor:")
print(descriptor.model_dump())
print("\nsource records:")
for record in records:
    print(record.model_dump())
