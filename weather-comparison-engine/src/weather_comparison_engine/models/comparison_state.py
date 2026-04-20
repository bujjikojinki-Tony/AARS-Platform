from __future__ import annotations

from pydantic import BaseModel

from weather_comparison_engine.models.dashboard_row import DashboardRow
from weather_comparison_engine.models.divergence_state import DivergenceState


class ComparisonState(BaseModel):
    market_id: str
    market_question: str | None = None

    location_name: str
    target_date: str
    variable_name: str

    model_band: str | None = None
    market_band: str | None = None
    model_value: float | None = None

    confidence_score: float
    divergence: DivergenceState
    action_hint: str

    def to_dashboard_row(self) -> DashboardRow:
        return DashboardRow(
            market_id=self.market_id,
            market_question=self.market_question,
            location_name=self.location_name,
            target_date=self.target_date,
            variable_name=self.variable_name,
            model_band=self.model_band,
            market_band=self.market_band,
            band_distance=self.divergence.band_distance,
            confidence_score=self.confidence_score,
            confidence_adjusted_gap=self.divergence.confidence_adjusted_gap,
            comparison_status=self.divergence.status,
            action_hint=self.action_hint,
        )
