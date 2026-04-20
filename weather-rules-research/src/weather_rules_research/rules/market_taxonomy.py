from __future__ import annotations

from dataclasses import dataclass

from weather_rules_research.registries.band_scheme_registry import resolve_band_scheme
from weather_rules_research.registries.source_registry import required_data_source_for_family
from weather_rules_research.rules.question_parser import parse_market_question


@dataclass(frozen=True)
class MarketTaxonomy:
    market_family: str
    primary_variable_name: str | None
    supported_by_current_pipeline: bool
    station_required: bool
    resolution_scope: str
    band_scheme: str | None = None
    required_data_source: str | None = None
    notes: str | None = None


def classify_market_question(question: str) -> MarketTaxonomy:
    q = (question or "").lower()
    parsed = parse_market_question(question or "")

    if parsed.variable_name in {"daily_max_temperature", "daily_min_temperature"}:
        market_family = "station_temperature"
        return MarketTaxonomy(
            market_family=market_family,
            primary_variable_name=parsed.variable_name,
            supported_by_current_pipeline=True,
            station_required=True,
            resolution_scope="station_weather",
            band_scheme=resolve_band_scheme(
                variable_name=parsed.variable_name,
                market_family=market_family,
            ),
            required_data_source=required_data_source_for_family(market_family),
            notes="Supported by Open-Meteo + station mapping.",
        )

    if parsed.variable_name == "daily_precipitation_sum":
        market_family = "weather_metric"
        return MarketTaxonomy(
            market_family=market_family,
            primary_variable_name=parsed.variable_name,
            supported_by_current_pipeline=True,
            station_required=True,
            resolution_scope="station_weather",
            band_scheme=resolve_band_scheme(
                variable_name=parsed.variable_name,
                market_family=market_family,
            ),
            required_data_source=required_data_source_for_family(market_family),
            notes="Supported for daily precipitation totals via Open-Meteo + station mapping.",
        )

    if parsed.variable_name == "daily_snowfall_sum":
        market_family = "weather_metric"
        return MarketTaxonomy(
            market_family=market_family,
            primary_variable_name=parsed.variable_name,
            supported_by_current_pipeline=True,
            station_required=True,
            resolution_scope="station_weather",
            band_scheme=resolve_band_scheme(
                variable_name=parsed.variable_name,
                market_family=market_family,
            ),
            required_data_source=required_data_source_for_family(market_family),
            notes="Supported for daily snowfall totals via Open-Meteo + station mapping.",
        )

    if parsed.variable_name == "daily_max_wind_speed":
        market_family = "weather_metric"
        return MarketTaxonomy(
            market_family=market_family,
            primary_variable_name=parsed.variable_name,
            supported_by_current_pipeline=True,
            station_required=True,
            resolution_scope="station_weather",
            band_scheme=resolve_band_scheme(
                variable_name=parsed.variable_name,
                market_family=market_family,
            ),
            required_data_source=required_data_source_for_family(market_family),
            notes="Supported for daily max wind speed via Open-Meteo + station mapping.",
        )

    if any(keyword in q for keyword in ("sea ice", "ice extent")):
        market_family = "sea_ice_extent"
        return MarketTaxonomy(
            market_family=market_family,
            primary_variable_name=None,
            supported_by_current_pipeline=True,
            station_required=False,
            resolution_scope="global_index",
            band_scheme=resolve_band_scheme(variable_name=None, market_family=market_family),
            required_data_source=required_data_source_for_family(market_family),
            notes="Supported by a sea ice extent snapshot feed.",
        )

    if parsed.market_type == "global_temperature_index_ordinal" or "hottest year" in q or "rank among the hottest years" in q:
        market_family = "global_temperature_index"
        return MarketTaxonomy(
            market_family=market_family,
            primary_variable_name=None,
            supported_by_current_pipeline=True,
            station_required=False,
            resolution_scope="global_index",
            band_scheme=resolve_band_scheme(variable_name=None, market_family=market_family),
            required_data_source=required_data_source_for_family(market_family),
            notes="Supported by a climate index snapshot feed.",
        )

    if any(keyword in q for keyword in ("precipitation", "rainfall", "snowfall", "wind", "humidity")):
        market_family = "weather_metric"
        return MarketTaxonomy(
            market_family=market_family,
            primary_variable_name=None,
            supported_by_current_pipeline=False,
            station_required=True,
            resolution_scope="station_weather",
            band_scheme=resolve_band_scheme(variable_name=None, market_family=market_family),
            required_data_source="station_weather_metric_source",
            notes="Needs a dedicated extractor for this weather metric.",
        )

    market_family = "unknown"
    return MarketTaxonomy(
        market_family=market_family,
        primary_variable_name=None,
        supported_by_current_pipeline=False,
        station_required=False,
        resolution_scope="unknown",
        band_scheme=resolve_band_scheme(variable_name=None, market_family=market_family),
        required_data_source=required_data_source_for_family(market_family),
        notes="Question pattern not recognized by the current taxonomy.",
    )
