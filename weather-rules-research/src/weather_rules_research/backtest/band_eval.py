from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass
class TemperatureBand:
    label: str
    lower: float | None = None
    upper: float | None = None
    lower_inclusive: bool = True
    upper_inclusive: bool = True

    def contains(self, value: float) -> bool:
        if self.lower is not None:
            if self.lower_inclusive:
                if value < self.lower:
                    return False
            else:
                if value <= self.lower:
                    return False

        if self.upper is not None:
            if self.upper_inclusive:
                if value > self.upper:
                    return False
            else:
                if value >= self.upper:
                    return False

        return True


class BandEvaluator:
    def __init__(self, bands: Sequence[TemperatureBand]) -> None:
        self.bands = list(bands)

    def classify(self, value: float) -> str | None:
        normalized_value = self._normalize_value(value)
        for band in self.bands:
            if band.contains(normalized_value):
                return band.label
        return None

    @staticmethod
    def _normalize_value(value: float) -> float:
        # Markets commonly resolve against whole-degree bands, so we normalize
        # floating-point temperatures to the nearest integer before band lookup.
        return float(int(value + 0.5))

    def hit(self, forecast_value: float, official_value: float) -> bool:
        forecast_band = self.classify(forecast_value)
        official_band = self.classify(official_value)

        if forecast_band is None or official_band is None:
            return False

        return forecast_band == official_band

    def adjacent_hit(self, forecast_value: float, official_value: float) -> bool:
        forecast_band = self.classify(forecast_value)
        official_band = self.classify(official_value)

        if forecast_band is None or official_band is None:
            return False

        labels = [band.label for band in self.bands]

        try:
            forecast_idx = labels.index(forecast_band)
            official_idx = labels.index(official_band)
        except ValueError:
            return False

        return abs(forecast_idx - official_idx) <= 1

    def extreme_miss(self, forecast_value: float, official_value: float, threshold: int = 2) -> bool:
        forecast_band = self.classify(forecast_value)
        official_band = self.classify(official_value)

        if forecast_band is None or official_band is None:
            return True

        labels = [band.label for band in self.bands]

        try:
            forecast_idx = labels.index(forecast_band)
            official_idx = labels.index(official_band)
        except ValueError:
            return True

        return abs(forecast_idx - official_idx) >= threshold
