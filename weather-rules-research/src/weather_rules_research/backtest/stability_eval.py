from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass
class StabilityRow:
    group_key: str
    forecast_value: float
    official_value: float

    @property
    def error(self) -> float:
        return self.forecast_value - self.official_value

    @property
    def absolute_error(self) -> float:
        return abs(self.error)


class StabilityEvaluator:
    """
    Evaluate whether forecast error is stable across groups such as:
    - station
    - city
    - month
    - season
    """

    def group_rows(self, rows: list[StabilityRow]) -> dict[str, list[StabilityRow]]:
        grouped: dict[str, list[StabilityRow]] = {}
        for row in rows:
            grouped.setdefault(row.group_key, []).append(row)
        return grouped

    def mean_error_by_group(self, rows: list[StabilityRow]) -> dict[str, float]:
        grouped = self.group_rows(rows)
        return {
            key: round(mean(item.error for item in bucket), 4)
            for key, bucket in grouped.items()
            if bucket
        }

    def mae_by_group(self, rows: list[StabilityRow]) -> dict[str, float]:
        grouped = self.group_rows(rows)
        return {
            key: round(mean(item.absolute_error for item in bucket), 4)
            for key, bucket in grouped.items()
            if bucket
        }

    def error_range_by_group(self, rows: list[StabilityRow]) -> dict[str, float]:
        grouped = self.group_rows(rows)
        results: dict[str, float] = {}

        for key, bucket in grouped.items():
            if not bucket:
                continue
            errors = [item.error for item in bucket]
            results[key] = round(max(errors) - min(errors), 4)

        return results

    def stable_groups(
        self,
        rows: list[StabilityRow],
        max_mae: float,
        max_error_range: float,
    ) -> list[str]:
        mae_map = self.mae_by_group(rows)
        range_map = self.error_range_by_group(rows)

        stable: list[str] = []
        for key in mae_map:
            if mae_map[key] <= max_mae and range_map.get(key, 9999.0) <= max_error_range:
                stable.append(key)

        return stable
