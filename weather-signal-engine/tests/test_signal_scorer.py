from weather_signal_engine.models.rule import Rule
from weather_signal_engine.models.forecast_state import ForecastState
from weather_signal_engine.models.market_snapshot import MarketSnapshot
from weather_signal_engine.scoring.signal_scorer import SignalScorer


def test_signal_scorer_generates_signal():
    scorer = SignalScorer()

    rule = Rule(
        market_id="m1",
        market_question="Highest temperature in Central Park on Apr 12?",
        market_type="daily_high_temperature",
        location_name="Central Park",
        target_date="2026-04-12",
        station_name="New York City Central Park",
        nws_station_id="KNYC",
        cdo_station_id="GHCND:USW00094728",
        variable_name="daily_max_temperature",
        timezone="America/New_York",
        source_name="official_source",
        parse_confidence=0.9,
        needs_review=False,
    )

    forecast_state = ForecastState(
        location_name="Central Park",
        target_date="2026-04-12",
        variable_name="daily_max_temperature",
        latest_forecast_value=28.1,
        source_mode="daily.temperature_2m_max",
        forecast_issued_at="2026-04-11T00:00:00",
        run_to_run_delta=0.2,
        model_band="28",
    )

    market_snapshot = MarketSnapshot(
        market_id="m1",
        market_question="Highest temperature in Central Park on Apr 12?",
        observed_at="2026-04-11T10:00:00",
        favored_band="27",
        implied_temperature_value=None,
        market_price_context=None,
        notes=None,
    )

    signal = scorer.score(rule, forecast_state, market_snapshot)

    assert signal.market_id == "m1"
    assert signal.model_band == "28"
    assert signal.market_band == "27"
    assert signal.confidence.score >= 0.5
