from __future__ import annotations

from uuid import uuid4

from backend.models.probability_governance import DisagreementLevel
from backend.models.probability_governance import ProbabilityComparisonView
from backend.models.probability_governance import ProbabilityEngineRun
from backend.models.probability_governance import ProbabilityEngineType


class ProbabilityComparisonBuilder:
    def build(self, runs: list[ProbabilityEngineRun]) -> ProbabilityComparisonView:
        if not runs:
            raise ValueError("cannot build ProbabilityComparisonView without engine runs")

        primary_runs = [run for run in runs if run.engine_type == ProbabilityEngineType.PRIMARY]
        if not primary_runs:
            raise ValueError("no primary engine run found")

        active_run = primary_runs[0]
        probabilities = [r.model_probability for r in runs]
        spread = max(probabilities) - min(probabilities)
        disagreement = self._resolve_disagreement(spread)
        warnings = ["Shadow engines are for comparison only and do not drive trading."]
        shadow_count = len([r for r in runs if r.engine_type == ProbabilityEngineType.SHADOW])
        if shadow_count == 0:
            warnings.append("No shadow engine runs were available.")

        return ProbabilityComparisonView(
            comparison_id=f"cmp_{uuid4().hex[:10]}",
            market_id=active_run.market_id,
            weather_view_id=active_run.weather_view_id,
            active_engine_id=active_run.engine_id,
            active_probability=active_run.model_probability,
            engine_runs=runs,
            spread_between_engines=spread,
            disagreement_level=disagreement,
            selection_reason=(
                f"{active_run.engine_id} selected because it is the accepted PRIMARY "
                "engine in PWB-03."
            ),
            warnings=warnings,
        )

    def _resolve_disagreement(self, spread: float) -> DisagreementLevel:
        if spread < 0.03:
            return DisagreementLevel.NONE
        if spread < 0.08:
            return DisagreementLevel.LOW
        if spread < 0.15:
            return DisagreementLevel.MEDIUM
        return DisagreementLevel.HIGH
