from __future__ import annotations

from datetime import date

import pytest

from weather_rules_research.models import ForecastSnapshot, MarketRule, Station
from weather_rules_research.governance import normalize_measurement
from weather_rules_research.open_meteo.client import OpenMeteoForecastClient
from weather_rules_research.open_meteo.extractors import ForecastExtractionResult
from weather_rules_research.open_meteo.forecast_poller import ForecastPoller


def test_normalize_measurement_uses_registry_policies() -> None:
    normalized = normalize_measurement(
        {"value": 32.0, "unit": "fahrenheit"},
        family="temperature_daily_max",
        variable_name="daily_max_temperature",
        band_scheme="temperature_4_bucket",
    )

    assert normalized["canonical_unit"] == "celsius"
    assert normalized["canonical_value"] == pytest.approx(0.0)
    assert normalized["display_value"] == pytest.approx(0.0)
    assert normalized["precision_policy_ref"] == "precision_policy.temperature_daily_max.v1"
    assert normalized["rounding_policy_ref"] == "rounding_policy.temperature_daily_max.v1"
    assert normalized["band_mapping_policy_ref"] == "band_mapping.temperature_celsius_integer.v1"


def test_open_meteo_forecast_stub_populates_normalization_fields() -> None:
    client = OpenMeteoForecastClient()
    rule = MarketRule(
        market_id="market-1",
        market_question="Highest temperature in Shanghai on Apr 20?",
        market_type="daily_high_temperature",
        location_name="Shanghai",
        target_date="Apr 20",
        station_name="Shanghai Pudong International Airport",
        nws_station_id="ZSPD",
        variable_name="daily_max_temperature",
        timezone="Asia/Shanghai",
        source_name="market_rules",
        raw_rules_text="Use official station observation.",
        parse_confidence=0.9,
        needs_review=False,
    )
    station = Station(
        station_name="Shanghai Pudong International Airport",
        nws_station_id="ZSPD",
        latitude=31.1443,
        longitude=121.8083,
        timezone="Asia/Shanghai",
        source="manual_station_map",
    )

    snapshot = client.fetch_forecast_stub(
        rule=rule,
        station=station,
        settlement_date=date(2026, 4, 20),
        predicted_temperature_c=29.44,
        issued_at="2026-04-20T09:00:00Z",
    )

    assert isinstance(snapshot, ForecastSnapshot)
    assert snapshot.raw_value == pytest.approx(29.44)
    assert snapshot.raw_unit == "celsius"
    assert snapshot.canonical_unit == "celsius"
    assert snapshot.display_value == pytest.approx(29.4)
    assert snapshot.precision_policy_ref == "precision_policy.temperature_daily_max.v1"
    assert snapshot.band_mapping_policy_ref == "band_mapping.temperature_celsius_integer.v1"
    assert snapshot.normalization_version == "measurement_normalization.v1"


@pytest.mark.anyio
async def test_forecast_poller_includes_normalization_fields() -> None:
    poller = ForecastPoller(
        latitude=31.1443,
        longitude=121.8083,
        target_date="2026-04-20",
        variable_name="daily_max_temperature",
    )

    async def _fake_fetch(*args, **kwargs):
        return {
            "daily": {
                "time": ["2026-04-20"],
                "temperature_2m_max": [29.44],
            }
        }

    poller.client.fetch = _fake_fetch  # type: ignore[method-assign]

    latest = await poller.poll_once()

    assert latest["value"] == pytest.approx(29.44)
    assert latest["raw_value"] == pytest.approx(29.44)
    assert latest["canonical_value"] == pytest.approx(29.44)
    assert latest["display_value"] == pytest.approx(29.4)
    assert latest["canonical_unit"] == "celsius"
    assert latest["precision_policy_ref"] == "precision_policy.temperature_daily_max.v1"
    assert latest["band_mapping_policy_ref"] == "band_mapping.temperature_celsius_integer.v1"
