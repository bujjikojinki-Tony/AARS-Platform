from pathlib import Path
import json
from tempfile import TemporaryDirectory

from weather_rules_research.models.market_rule import MarketRule
from weather_rules_research.stations.mapper import StationMapper


def test_station_mapper_returns_dual_ids() -> None:
    sample_payload = [
        {
            "canonical_location": "Central Park",
            "selected_station": {
                "station_name": "New York City Central Park",
                "nws_station_id": "KNYC",
                "cdo_station_id": "GHCND:USW00094728",
                "latitude": 40.78,
                "longitude": -73.97,
                "timezone": "America/New_York",
                "source": "manual_whitelist",
            },
            "aliases": ["NYC Central Park"],
            "mapping_method": "manual_whitelist",
            "mapping_confidence": 0.99,
        }
    ]

    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "manual_station_map.json"
        path.write_text(json.dumps(sample_payload), encoding="utf-8")

        mapper = StationMapper(str(path))

        rule = MarketRule(
            market_id="m1",
            market_question="Highest temperature in Central Park on Apr 12?",
            market_type="daily_high_temperature",
            location_name="Central Park",
            target_date="2026-04-12",
            station_name=None,
            nws_station_id=None,
            cdo_station_id=None,
            variable_name="daily_max_temperature",
            timezone="America/New_York",
            source_name="market_rules",
            raw_rules_text="stub",
            parse_confidence=0.9,
            needs_review=False,
        )

        station = mapper.map_rule_to_station(rule)

        assert station is not None
        assert station.nws_station_id == "KNYC"
        assert station.cdo_station_id == "GHCND:USW00094728"
