from __future__ import annotations

from backend.models.core import MarketSnapshot
from backend.normalization.market_question_parser import parse_market_question
from backend.normalization.weather_market_resolver import resolve_weather_market


def test_parse_market_question_extracts_city_date_threshold_direction_above() -> None:
    market = MarketSnapshot(
        market_id="mkt_tokyo_temp",
        question="Will Tokyo high temperature exceed 30C on 2026-05-01?",
        yes_price=0.52,
        no_price=0.48,
        liquidity=1000,
        spread=0.03,
    )

    descriptor = parse_market_question(market)

    assert descriptor.city == "Tokyo"
    assert descriptor.target_date == "2026-05-01"
    assert descriptor.threshold == 30.0
    assert descriptor.direction == "ABOVE"
    assert descriptor.measurement == "C"


def test_parse_market_question_extracts_below_direction() -> None:
    market = MarketSnapshot(
        market_id="mkt_oslo_temp",
        question="Will max temperature in Oslo fall below -5C on 2026-12-02?",
        yes_price=0.31,
        no_price=0.69,
        liquidity=500,
        spread=0.04,
    )

    descriptor = parse_market_question(market)

    assert descriptor.city == "Oslo"
    assert descriptor.target_date == "2026-12-02"
    assert descriptor.threshold == -5.0
    assert descriptor.direction == "BELOW"


def test_resolver_returns_weather_market_descriptor() -> None:
    market = MarketSnapshot(
        market_id="mkt_ny_rain",
        question="Will rainfall exceed 50mm in New York on 2026-04-29?",
        yes_price=0.41,
        no_price=0.59,
        liquidity=120000,
        spread=0.03,
    )

    descriptor = resolve_weather_market(market)

    assert descriptor.market_id == "mkt_ny_rain"
    assert descriptor.city == "New York"
    assert descriptor.target_date == "2026-04-29"
    assert descriptor.threshold == 50.0
    assert descriptor.direction == "ABOVE"
