from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass
class ForecastDriftRow:
    forecast_issued_date: str
    target_date: str
    lead_days: int
    forecast_value: float
    official_value: float

    @property
    def error(self) -> float:
        return self.forecast_value - self.official_value


class DriftEvaluator:
    """
    Evaluate how forecast error changes across different lead times.

    Example lead buckets:
    - T-7
    - T-5
    - T-3
    - T-1
    - T-0
    """

    def group_by_lead_days(self, rows: list[ForecastDriftRow]) -> dict[int, list[ForecastDriftRow]]:
        grouped: dict[int, list[ForecastDriftRow]] = {}
        for row in rows:
            grouped.setdefault(row.lead_days, []).append(row)
        return grouped

    def mean_error_by_lead(self, rows: list[ForecastDriftRow]) -> dict[int, float]:
        grouped = self.group_by_lead_days(rows)
        return {
            lead: round(mean(item.error for item in bucket), 3)
            for lead, bucket in grouped.items()
            if bucket
        }

    def mae_by_lead(self, rows: list[ForecastDriftRow]) -> dict[int, float]:
        grouped = self.group_by_lead_days(rows)
        return {
            lead: round(mean(abs(item.error) for item in bucket), 3)
            for lead, bucket in grouped.items()
            if bucket
        }

    def rmse_by_lead(self, rows: list[ForecastDriftRow]) -> dict[int, float]:
        grouped = self.group_by_lead_days(rows)
        return {
            lead: round((mean((item.error ** 2) for item in bucket) ** 0.5), 3)
            for lead, bucket in grouped.items()
            if bucket
        }

    def forecast_trend_for_target(
        self,
        rows: list[ForecastDriftRow],
        target_date: str,
    ) -> list[ForecastDriftRow]:
        filtered = [row for row in rows if row.target_date == target_date]
        return sorted(filtered, key=lambda x: x.lead_days, reverse=True)

    def drift_span_for_target(self, rows: list[ForecastDriftRow], target_date: str) -> float | None:
        trend = self.forecast_trend_for_target(rows, target_date)
        if len(trend) < 2:
            return None
        values = [row.forecast_value for row in trend]
        return round(max(values) - min(values), 3)
