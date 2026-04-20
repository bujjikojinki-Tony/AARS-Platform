from pydantic import BaseModel


class DashboardRow(BaseModel):
    market_id: str
    market_question: str | None = None

    location_name: str
    target_date: str
    variable_name: str

    model_band: str | None = None
    market_band: str | None = None

    band_distance: int
    confidence_score: float
    confidence_adjusted_gap: float

    comparison_status: str
    action_hint: str
