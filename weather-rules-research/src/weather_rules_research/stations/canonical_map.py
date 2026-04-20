from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CanonicalStationMapping:
    canonical_location: str
    selected_station: dict
    aliases: list[str]
    mapping_method: str
    mapping_confidence: float


class CanonicalMapRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> list[CanonicalStationMapping]:
        if not self.path.exists():
            return []

        payload = json.loads(self.path.read_text(encoding="utf-8"))
        results: list[CanonicalStationMapping] = []

        for item in payload:
            if "canonical_location" not in item:
                canonical_location = (
                    item.get("station_name")
                    or item.get("location_name")
                    or item.get("market_question")
                    or "unknown"
                )
                selected_station = {
                    "station_name": item.get("station_name") or canonical_location,
                    "nws_station_id": item.get("nws_station_id"),
                    "cdo_station_id": item.get("cdo_station_id"),
                    "latitude": item.get("latitude"),
                    "longitude": item.get("longitude"),
                    "timezone": item.get("timezone"),
                    "source": item.get("source", "manual_whitelist"),
                }
                results.append(
                    CanonicalStationMapping(
                        canonical_location=canonical_location,
                        selected_station=selected_station,
                        aliases=item.get("aliases", []),
                        mapping_method=item.get("mapping_method", item.get("source", "manual_whitelist")),
                        mapping_confidence=float(item.get("mapping_confidence", 1.0)),
                    )
                )
                continue

            results.append(
                CanonicalStationMapping(
                    canonical_location=item["canonical_location"],
                    selected_station=item["selected_station"],
                    aliases=item.get("aliases", []),
                    mapping_method=item.get("mapping_method", "manual_whitelist"),
                    mapping_confidence=float(item.get("mapping_confidence", 1.0)),
                )
            )

        return results

    def load_index(self) -> dict[str, CanonicalStationMapping]:
        mappings = self.load()
        index: dict[str, CanonicalStationMapping] = {}

        for mapping in mappings:
            index[mapping.canonical_location.lower()] = mapping
            for alias in mapping.aliases:
                index[alias.lower()] = mapping

        return index
