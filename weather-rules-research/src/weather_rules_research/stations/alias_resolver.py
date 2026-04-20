from __future__ import annotations

import re

from weather_rules_research.stations.canonical_map import CanonicalStationMapping


class AliasResolver:
    """
    Resolve raw market location names to canonical locations.

    Resolution strategy:
    1. exact lowercase match
    2. normalized match
    3. alias index lookup
    """

    def __init__(self, alias_index: dict[str, CanonicalStationMapping]) -> None:
        self.alias_index = alias_index

    @staticmethod
    def normalize(text: str) -> str:
        text = text.strip().lower()
        text = text.replace("nyc", "new york city")
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def resolve(self, raw_location: str) -> CanonicalStationMapping | None:
        if not raw_location:
            return None

        exact = raw_location.lower()
        if exact in self.alias_index:
            return self.alias_index[exact]

        normalized = self.normalize(raw_location)
        if normalized in self.alias_index:
            return self.alias_index[normalized]

        for key, mapping in self.alias_index.items():
            if self.normalize(key) == normalized:
                return mapping

        return None
