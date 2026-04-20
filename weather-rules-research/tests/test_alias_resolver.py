from weather_rules_research.stations.alias_resolver import AliasResolver
from weather_rules_research.stations.canonical_map import CanonicalStationMapping


def build_alias_index() -> dict[str, CanonicalStationMapping]:
    mapping = CanonicalStationMapping(
        canonical_location="Central Park",
        selected_station={
            "station_name": "New York City Central Park",
            "nws_station_id": "KNYC",
            "cdo_station_id": "GHCND:USW00094728",
            "latitude": 40.78,
            "longitude": -73.97,
            "timezone": "America/New_York",
            "source": "manual_whitelist",
        },
        aliases=[
            "NYC Central Park",
            "New York Central Park",
            "Central Park NYC",
        ],
        mapping_method="manual_whitelist",
        mapping_confidence=0.99,
    )

    return {
        "central park": mapping,
        "nyc central park": mapping,
        "new york central park": mapping,
        "central park nyc": mapping,
    }


def test_alias_resolver_exact_match() -> None:
    resolver = AliasResolver(build_alias_index())
    result = resolver.resolve("central park")

    assert result is not None
    assert result.canonical_location == "Central Park"


def test_alias_resolver_alias_match() -> None:
    resolver = AliasResolver(build_alias_index())
    result = resolver.resolve("NYC Central Park")

    assert result is not None
    assert result.canonical_location == "Central Park"


def test_alias_resolver_normalized_match() -> None:
    resolver = AliasResolver(build_alias_index())
    result = resolver.resolve("Central Park, NYC")

    assert result is not None
    assert result.canonical_location == "Central Park"


def test_alias_resolver_returns_none_when_not_found() -> None:
    resolver = AliasResolver(build_alias_index())
    result = resolver.resolve("Unknown Location")

    assert result is None
