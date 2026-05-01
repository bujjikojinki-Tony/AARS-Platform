from __future__ import annotations

from backend.models.core import MarketSnapshot
from backend.models.weather import WeatherMarketDescriptor
from .market_question_parser import parse_market_question


def resolve_weather_market(market: MarketSnapshot) -> WeatherMarketDescriptor:
    return parse_market_question(market)
