from pydantic import BaseModel


class TimeSeriesPoint(BaseModel):
    timestamp: str
    market_id: str

    model_value: float | None = None
    model_band: str | None = None

    market_band: str | None = None
    market_probability: float | None = None

    confidence_adjusted_gap: float | None = None
