from pathlib import Path
import json
from tempfile import TemporaryDirectory

from weather_rules_research.models import MarketRule
from weather_rules_research.stations import AliasResolver, CanonicalMapRepository, StationMapper


def test_station_mapper_loads_manual_station_json_and_resolves_alias() -> None:
    mapping_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "processed"
        / "station_maps"
        / "manual_station_map.json"
    )
    mapper = StationMapper(str(mapping_path))
    rule = MarketRule(
        market_id="market-1",
        market_question="Lowest temperature in Central Park NYC on Mar 15?",
        market_type="daily_low_temperature",
        location_name="Central Park NYC",
        target_date="Mar 15",
        station_name=None,
        nws_station_id=None,
        cdo_station_id=None,
        variable_name="daily_min_temperature",
        timezone="America/New_York",
        source_name="market_rules",
        raw_rules_text="Resolves according to the lowest temperature recorded by the official station.",
        parse_confidence=0.95,
        needs_review=False,
    )

    station = mapper.map_rule_to_station(rule)

    assert station is not None
    assert station.nws_station_id == "KNYC"
    assert station.cdo_station_id == "GHCND:USW00094728"
    assert station.timezone == "America/New_York"
    assert station.source == "manual_whitelist"


def test_canonical_map_repository_loads_alias_index() -> None:
    mapping_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "processed"
        / "station_maps"
        / "manual_station_map.json"
    )
    repository = CanonicalMapRepository(mapping_path)

    index = repository.load_index()

    assert "central park" in index
    assert "central park nyc" in index
    assert index["central park"].selected_station["nws_station_id"] == "KNYC"


def test_alias_resolver_expands_nyc_variant() -> None:
    mapping_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "processed"
        / "station_maps"
        / "manual_station_map.json"
    )
    repository = CanonicalMapRepository(mapping_path)
    resolver = AliasResolver(repository.load_index())

    mapping = resolver.resolve("Central Park, NYC")

    assert mapping is not None
    assert mapping.selected_station["nws_station_id"] == "KNYC"


def test_canonical_map_repository_supports_legacy_station_map_schema() -> None:
    legacy_payload = [
        {
            "station_name": "New York City Central Park",
            "nws_station_id": "KNYC",
            "cdo_station_id": "GHCND:USW00094728",
            "latitude": 40.78,
            "longitude": -73.97,
            "timezone": "America/New_York",
            "source": "manual_whitelist",
        }
    ]

    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "manual_station_map.json"
        path.write_text(json.dumps(legacy_payload), encoding="utf-8")

        repository = CanonicalMapRepository(path)
        index = repository.load_index()

    assert "new york city central park" in index
    assert index["new york city central park"].selected_station["station_name"] == "New York City Central Park"


def test_station_mapper_resolves_shanghai_to_pudong_airport() -> None:
    mapping_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "processed"
        / "station_maps"
        / "manual_station_map.json"
    )
    mapper = StationMapper(str(mapping_path))
    rule = MarketRule(
        market_id="market-shanghai-1",
        market_question="Highest temperature in Shanghai on Apr 14?",
        market_type="daily_high_temperature",
        location_name="Shanghai",
        target_date="Apr 14",
        station_name=None,
        nws_station_id=None,
        cdo_station_id=None,
        variable_name="daily_max_temperature",
        timezone="Asia/Shanghai",
        source_name="market_rules",
        raw_rules_text="Resolves based on the official highest temperature recorded at Shanghai Pudong International Airport station.",
        parse_confidence=0.93,
        needs_review=False,
    )

    station = mapper.map_rule_to_station(rule)

    assert station is not None
    assert station.station_name == "Shanghai Pudong International Airport"
    assert station.timezone == "Asia/Shanghai"
    assert station.source == "wunderground:zspd"
