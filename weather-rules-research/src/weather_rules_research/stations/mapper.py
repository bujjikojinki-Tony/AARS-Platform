from __future__ import annotations

from weather_rules_research.models import MarketRule, Station
from weather_rules_research.stations.alias_resolver import AliasResolver
from weather_rules_research.stations.canonical_map import CanonicalMapRepository


class StationMapper:
    def __init__(self, canonical_map_path: str) -> None:
        repo = CanonicalMapRepository(canonical_map_path)
        self.alias_index = repo.load_index()
        self.alias_resolver = AliasResolver(self.alias_index)

    def map_rule_to_station(self, rule: MarketRule) -> Station | None:
        mapping = self.alias_resolver.resolve(rule.location_name)
        if mapping is None:
            return None

        station_payload = mapping.selected_station
        return Station(
            station_name=station_payload["station_name"],
            nws_station_id=station_payload.get("nws_station_id"),
            cdo_station_id=station_payload.get("cdo_station_id"),
            latitude=station_payload["latitude"],
            longitude=station_payload["longitude"],
            timezone=station_payload.get("timezone"),
            source=station_payload.get("source", "manual_whitelist"),
        )
