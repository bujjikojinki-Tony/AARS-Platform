import pytest

from weather_rules_research.models.market_rule import MarketRule
from weather_rules_research.official_obs.station_settlement_backfill import (
    StationSettlementBackfiller,
    build_station_backfill_summary,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_station_settlement_backfill_uses_sample_official_value():
    backfiller = StationSettlementBackfiller()

    records = await backfiller.backfill_records(
        rules=[
            MarketRule(
                market_id="sample_market_001",
                market_question="Highest temperature in Central Park on Apr 12?",
                market_type="daily_high_temperature",
                location_name="Central Park",
                target_date="Apr 12",
                station_name="New York City Central Park",
                nws_station_id="KNYC",
                cdo_station_id="GHCND:USW00094728",
                variable_name="daily_max_temperature",
                timezone="America/New_York",
                source_name="market_rules",
                raw_rules_text="Resolves using official station data from Central Park in New York time for the daily high.",
                parse_confidence=0.92,
                needs_review=False,
            )
        ],
        scenarios=[
            {
                "market_id": "sample_market_001",
                "target_date": "2026-04-12",
                "official_value": 28.0,
                "expected_band": "28",
                "source": "sample.station_settlement",
            }
        ],
    )

    assert len(records) == 1
    record = records[0]
    assert record["station_id"] == "KNYC"
    assert record["official_value"] == 28.0
    assert record["resolved_band"] == "28"
    assert record["source"] == "sample.station_settlement"


class _FakeFetcher:
    async def fetch_daily_value(self, station_id: str, target_date: str, variable_name: str) -> dict:
        return {
            "station_id": station_id,
            "target_date": target_date,
            "variable_name": variable_name,
            "official_value": 27.0,
            "unit": "celsius",
            "source": "ncei_cdo_daily",
            "source_url": "https://example.com",
            "raw_payload_ref": "raw://payload",
        }


@pytest.mark.anyio
async def test_station_settlement_backfill_can_use_fetcher():
    backfiller = StationSettlementBackfiller(fetcher=_FakeFetcher())

    records = await backfiller.backfill_records(
        rules=[
            MarketRule(
                market_id="sample_market_002",
                market_question="Highest temperature in Central Park on Apr 13?",
                market_type="daily_high_temperature",
                location_name="Central Park",
                target_date="Apr 13",
                station_name="New York City Central Park",
                nws_station_id="KNYC",
                cdo_station_id="GHCND:USW00094728",
                variable_name="daily_max_temperature",
                timezone="America/New_York",
                source_name="market_rules",
                raw_rules_text="Resolves using official station data from Central Park in New York time for the daily high.",
                parse_confidence=0.92,
                needs_review=False,
            )
        ],
        scenarios=[
            {
                "market_id": "sample_market_002",
                "target_date": "2026-04-13",
                "expected_band": "27",
            }
        ],
        enable_fetch=True,
    )

    assert len(records) == 1
    record = records[0]
    assert record["official_value"] == 27.0
    assert record["resolved_band"] == "27"
    assert record["source"] == "ncei_cdo_daily"


def test_station_backfill_summary_reports_counts():
    summary = build_station_backfill_summary(
        [
            {
                "market_id": "sample_market_001",
                "market_family": "station_temperature",
                "source": "sample.station_settlement",
                "label_type": "settlement_grade",
            },
            {
                "market_id": "sample_market_002",
                "market_family": "station_temperature",
                "source": "ncei_cdo_daily",
                "label_type": "settlement_grade",
            },
        ],
        fetch_enabled=True,
    )

    assert summary["fetch_enabled"] is True
    assert summary["record_count"] == 2
    assert summary["market_family_counts"]["station_temperature"] == 2
    assert summary["source_counts"]["sample.station_settlement"] == 1
    assert summary["source_counts"]["ncei_cdo_daily"] == 1
