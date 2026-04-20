from pydantic import BaseModel


class DivergenceState(BaseModel):
    status: str
    band_distance: int
    confidence_adjusted_gap: float
