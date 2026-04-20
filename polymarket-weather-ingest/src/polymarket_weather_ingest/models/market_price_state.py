from pydantic import BaseModel


class MarketPriceState(BaseModel):
    observed_at: str | None = None
    favored_outcome: str | None = None
    favored_probability: float | None = None
    implied_band: str | None = None
    notes: str | None = None
