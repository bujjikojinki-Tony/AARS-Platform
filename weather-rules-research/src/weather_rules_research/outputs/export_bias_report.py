from __future__ import annotations

import csv
from pathlib import Path
from typing import Sequence

from weather_rules_research.backtest.band_eval import BandEvaluator
from weather_rules_research.backtest.bias_eval import BiasEvaluator
from weather_rules_research.backtest.drift_eval import DriftEvaluator, ForecastDriftRow
from weather_rules_research.backtest.joiner import JoinedForecastSettlement
from weather_rules_research.backtest.stability_eval import StabilityEvaluator, StabilityRow


class BiasReportExporter:
    def __init__(
        self,
        bias_evaluator: BiasEvaluator | None = None,
        drift_evaluator: DriftEvaluator | None = None,
        stability_evaluator: StabilityEvaluator | None = None,
        band_evaluator: BandEvaluator | None = None,
    ) -> None:
        self.bias_evaluator = bias_evaluator or BiasEvaluator()
        self.drift_evaluator = drift_evaluator or DriftEvaluator()
        self.stability_evaluator = stability_evaluator or StabilityEvaluator()
        self.band_evaluator = band_evaluator

    def export_summary_report(
        self,
        path: Path,
        joined_rows: Sequence[JoinedForecastSettlement],
        drift_rows: Sequence[ForecastDriftRow] | None = None,
        stability_rows: Sequence[StabilityRow] | None = None,
    ) -> None:
        drift_rows = list(drift_rows or [])
        stability_rows = list(stability_rows or [])

        mean_error = self.bias_evaluator.mean_error(list(joined_rows))
        mae = self.bias_evaluator.mean_absolute_error(list(joined_rows))
        rmse = self._rmse(joined_rows)

        band_hit_rate = self._band_hit_rate(joined_rows)
        adjacent_hit_rate = self._adjacent_hit_rate(joined_rows)
        extreme_miss_rate = self._extreme_miss_rate(joined_rows)

        drift_spans = self._drift_spans_by_target(drift_rows)
        avg_drift_span = sum(drift_spans.values()) / len(drift_spans) if drift_spans else None

        stable_groups = self._stable_groups(stability_rows)

        rows = [
            ("metric", "value"),
            ("count_rows", len(joined_rows)),
            ("mean_error", mean_error),
            ("mae", mae),
            ("rmse", rmse),
            ("band_hit_rate", band_hit_rate),
            ("adjacent_hit_rate", adjacent_hit_rate),
            ("extreme_miss_rate", extreme_miss_rate),
            ("avg_drift_span", avg_drift_span),
            ("stable_groups_count", len(stable_groups)),
            ("stable_groups", ";".join(stable_groups) if stable_groups else ""),
        ]

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    def export_drift_detail_report(
        self,
        path: Path,
        drift_rows: Sequence[ForecastDriftRow],
    ) -> None:
        mae_by_lead = self.drift_evaluator.mae_by_lead(list(drift_rows))
        mean_error_by_lead = self.drift_evaluator.mean_error_by_lead(list(drift_rows))
        rmse_by_lead = self.drift_evaluator.rmse_by_lead(list(drift_rows))

        leads = sorted(set(mae_by_lead.keys()) | set(mean_error_by_lead.keys()) | set(rmse_by_lead.keys()))

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["lead_days", "mean_error", "mae", "rmse"])
            for lead in leads:
                writer.writerow([
                    lead,
                    mean_error_by_lead.get(lead),
                    mae_by_lead.get(lead),
                    rmse_by_lead.get(lead),
                ])

    def export_stability_detail_report(
        self,
        path: Path,
        stability_rows: Sequence[StabilityRow],
    ) -> None:
        mean_error_by_group = self.stability_evaluator.mean_error_by_group(list(stability_rows))
        mae_by_group = self.stability_evaluator.mae_by_group(list(stability_rows))
        error_range_by_group = self.stability_evaluator.error_range_by_group(list(stability_rows))

        groups = sorted(
            set(mean_error_by_group.keys())
            | set(mae_by_group.keys())
            | set(error_range_by_group.keys())
        )

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["group_key", "mean_error", "mae", "error_range"])
            for group in groups:
                writer.writerow([
                    group,
                    mean_error_by_group.get(group),
                    mae_by_group.get(group),
                    error_range_by_group.get(group),
                ])

    def _rmse(self, rows: Sequence[JoinedForecastSettlement]) -> float:
        return self.bias_evaluator.rmse(rows)

    def _band_hit_rate(self, rows: Sequence[JoinedForecastSettlement]) -> float | None:
        if not self.band_evaluator or not rows:
            return None
        hits = [
            self.band_evaluator.hit(row.forecast_value, row.official_value)
            for row in rows
        ]
        return round(sum(1 for x in hits if x) / len(hits), 4)

    def _adjacent_hit_rate(self, rows: Sequence[JoinedForecastSettlement]) -> float | None:
        if not self.band_evaluator or not rows:
            return None
        hits = [
            self.band_evaluator.adjacent_hit(row.forecast_value, row.official_value)
            for row in rows
        ]
        return round(sum(1 for x in hits if x) / len(hits), 4)

    def _extreme_miss_rate(self, rows: Sequence[JoinedForecastSettlement]) -> float | None:
        if not self.band_evaluator or not rows:
            return None
        misses = [
            self.band_evaluator.extreme_miss(row.forecast_value, row.official_value)
            for row in rows
        ]
        return round(sum(1 for x in misses if x) / len(misses), 4)

    def _drift_spans_by_target(
        self,
        rows: Sequence[ForecastDriftRow],
    ) -> dict[str, float]:
        targets = sorted(set(row.target_date for row in rows))
        result: dict[str, float] = {}
        for target in targets:
            span = self.drift_evaluator.drift_span_for_target(list(rows), target)
            if span is not None:
                result[target] = span
        return result

    def _stable_groups(self, rows: Sequence[StabilityRow]) -> list[str]:
        if not rows:
            return []
        return self.stability_evaluator.stable_groups(
            list(rows),
            max_mae=1.0,
            max_error_range=2.0,
        )
