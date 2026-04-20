from __future__ import annotations

import math
from statistics import mean
from typing import Sequence

from weather_rules_research.backtest.joiner import JoinedForecastSettlement


class BiasEvaluator:
    def mean_error(self, rows: Sequence[JoinedForecastSettlement]) -> float:
        if not rows:
            return 0.0
        return round(mean(row.error for row in rows), 4)

    def mean_absolute_error(self, rows: Sequence[JoinedForecastSettlement]) -> float:
        if not rows:
            return 0.0
        return round(mean(abs(row.error) for row in rows), 4)

    def rmse(self, rows: Sequence[JoinedForecastSettlement]) -> float:
        if not rows:
            return 0.0
        return round(math.sqrt(mean((row.error ** 2) for row in rows)), 4)
