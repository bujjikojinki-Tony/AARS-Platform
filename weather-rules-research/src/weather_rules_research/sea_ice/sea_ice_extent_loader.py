from __future__ import annotations

import json
from pathlib import Path


class SeaIceExtentLoader:
    def load(self, path: str | Path) -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8"))


def extract_sea_ice_extent_value(snapshot: dict | None) -> float | None:
    if not isinstance(snapshot, dict):
        return None

    for key in ("minimum_extent", "extent", "value"):
        value = snapshot.get(key)
        try:
            if value is not None and value != "":
                return float(value)
        except (TypeError, ValueError):
            continue

    return None


def classify_sea_ice_band(
    value: float | None,
    *,
    lower: float | None,
    upper: float | None,
) -> str | None:
    if value is None:
        return None
    if lower is not None and value < lower:
        return "below_range"
    if upper is not None and value > upper:
        return "above_range"
    return "in_range"
