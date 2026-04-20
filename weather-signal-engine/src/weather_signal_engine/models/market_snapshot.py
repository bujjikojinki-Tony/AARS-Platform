from pydantic import BaseModel


class MarketSnapshot(BaseModel):
    market_id: str
    market_question: str
    observed_at: str

    favored_band: str | None = None
    implied_temperature_value: float | None = None
    market_price_context: float | None = None

    notes: str | None = None
