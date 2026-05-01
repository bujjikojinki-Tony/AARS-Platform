from __future__ import annotations

from backend.models.core import MarketSnapshot
from backend.models.weather import ProbabilityView
from backend.weather.evidence_pack_builder import EvidencePackBuilder
from backend.weather.market_question_parser import MarketQuestionParser
from backend.weather.noaa_source import NoaaPlaceholderSource
from backend.weather.open_meteo_source import OpenMeteoSource
from backend.weather.source_health_checker import SourceHealthChecker
from backend.weather.weather_market_resolver import WeatherMarketResolver
from backend.weather.weather_source_registry import WeatherSourceRegistry
from backend.weather.weather_view_builder import WeatherViewBuilder
from backend.probability.probability_view_builder import ProbabilityViewBuilder
from backend.archive.weather_forecast_archive_service import WeatherForecastArchiveService


class WeatherProbabilityProvider:
    """Convert a market snapshot into a Gaussian weather probability."""

    def __init__(
        self,
        repository=None,
        default_year: int | None = None,
        allow_network: bool = False,
        default_sigma: float = 2.5,
        archive_weather_on_probability_build: bool = False,
    ):
        self.repository = repository
        self.archive_weather_on_probability_build = archive_weather_on_probability_build
        self.parser = MarketQuestionParser(default_year=default_year or 2026)
        self.resolver = WeatherMarketResolver()
        self.registry = WeatherSourceRegistry(
            sources=[
                OpenMeteoSource(allow_network=allow_network),
                NoaaPlaceholderSource(),
            ]
        )
        self.health_checker = SourceHealthChecker()
        self.evidence_builder = EvidencePackBuilder()
        self.weather_view_builder = WeatherViewBuilder(default_sigma=default_sigma)
        self.probability_view_builder = ProbabilityViewBuilder()
        self.weather_archive_service = (
            WeatherForecastArchiveService(repository) if repository is not None else None
        )

    def estimate(self, market: MarketSnapshot) -> float:
        return self.build_probability_view(market).model_probability

    def build_probability_view(self, market: MarketSnapshot) -> ProbabilityView:
        descriptor = self.parser.parse(market.market_id, market.question)
        descriptor = self.resolver.resolve(descriptor)
        if self.repository is not None:
            self.repository.save_weather_descriptor(descriptor)

        source_records = []
        for source in self.registry.select_sources(descriptor):
            record = source.fetch(descriptor)
            record = self.health_checker.check(record)
            source_records.append(record)
            if self.repository is not None:
                self.repository.save_weather_source(record)

        evidence_pack = self.evidence_builder.build(descriptor, source_records)
        if self.repository is not None:
            self.repository.save_evidence_pack(evidence_pack)

        weather_view = self.weather_view_builder.build(evidence_pack)
        if self.repository is not None:
            self.repository.save_weather_view(weather_view)

        probability_view = self.probability_view_builder.build(weather_view)
        if self.repository is not None:
            self.repository.save_probability_view(probability_view)

        if (
            self.repository is not None
            and self.archive_weather_on_probability_build
            and self.weather_archive_service is not None
        ):
            try:
                self.weather_archive_service.archive_probability_build_bundle(
                    weather_view=weather_view,
                    evidence_pack=evidence_pack,
                    source_records=source_records,
                    metadata={
                        "capture_source": "probability_build",
                        "does_not_change_probability": True,
                    },
                )
            except Exception:
                pass

        return probability_view
