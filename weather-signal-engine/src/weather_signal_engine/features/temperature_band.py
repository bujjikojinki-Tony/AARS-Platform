from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


def classify_temperature_band(value: float) -> str:
    rounded = round(value)
    if rounded <= 26:
        return "26_or_below"
    if rounded == 27:
        return "27"
    if rounded == 28:
        return "28"
    return "29_plus"


@dataclass(frozen=True)
class TemperatureBand:
    label: str
    lower: float | None = None
    upper: float | None = None
    lower_inclusive: bool = True
    upper_inclusive: bool = True

    def contains(self, value: float) -> bool:
        rounded = round(value)
        if self.lower is not None:
            if self.lower_inclusive and rounded < self.lower:
                return False
            if not self.lower_inclusive and rounded <= self.lower:
                return False
        if self.upper is not None:
            if self.upper_inclusive and rounded > self.upper:
                return False
            if not self.upper_inclusive and rounded >= self.upper:
                return False
        return True


class TemperatureBandClassifier:
    def __init__(self, bands: Sequence[TemperatureBand]) -> None:
        self.bands = list(bands)

    def classify(self, value: float) -> str | None:
        for band in self.bands:
            if band.contains(value):
                return band.label
        return None
