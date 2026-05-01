from __future__ import annotations

from uuid import uuid4

from backend.models.probability_governance import MarketOutcome
from backend.models.probability_governance import OutcomeStatus


class MarketOutcomeService:
    def __init__(self, repository):
        self.repository = repository

    def record_outcome(
        self,
        market_id: str,
        status: str,
        resolved_direction_hit: bool | None = None,
        resolved_value: float | None = None,
        official_source: str | None = None,
        notes: str | None = None,
    ) -> MarketOutcome:
        outcome = MarketOutcome(
            outcome_id=f"out_{uuid4().hex[:10]}",
            market_id=market_id,
            resolved_value=resolved_value,
            resolved_direction_hit=resolved_direction_hit,
            official_source=official_source,
            status=OutcomeStatus(status),
            notes=notes,
        )
        self.repository.save_market_outcome(outcome)
        return outcome

    def get_latest_outcome(self, market_id: str) -> dict | None:
        return self.repository.get_latest_market_outcome(market_id)

    def is_calibratable(self, outcome: dict | MarketOutcome | None) -> bool:
        if outcome is None:
            return False
        if isinstance(outcome, MarketOutcome):
            return (
                outcome.status == OutcomeStatus.RESOLVED
                and outcome.resolved_direction_hit is not None
            )
        return (
            outcome.get("status") == OutcomeStatus.RESOLVED.value
            and outcome.get("resolved_direction_hit") is not None
        )
