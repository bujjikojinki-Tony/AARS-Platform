from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from weather_rules_research.models.station import Station


def export_station_map(path: Path, stations: Sequence[Station]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([station.model_dump(mode="json") for station in stations], indent=2),
        encoding="utf-8",
    )
