from pydantic import BaseModel


class MarketDetailState(BaseModel):
    market_id: str
    market_question: str | None = None
    location_name: str | None = None
    target_date: str | None = None
    variable_name: str | None = None

    model_band: str | None = None
    market_band: str | None = None

    confidence_score: float | None = None
    confidence_adjusted_gap: float | None = None
    comparison_status: str | None = None
    action_hint: str | None = None
