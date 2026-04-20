from pydantic import BaseModel


class ComparisonHistoryPoint(BaseModel):
    timestamp: str
    market_id: str

    model_band: str | None = None
    market_band: str | None = None

    confidence_score: float | None = None
    confidence_adjusted_gap: float | None = None
    comparison_status: str | None = None
    action_hint: str | None = None
