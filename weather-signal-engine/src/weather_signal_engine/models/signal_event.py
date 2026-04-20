from pydantic import BaseModel

from weather_signal_engine.models.confidence import Confidence


class SignalEvent(BaseModel):
    signal_id: str
    market_id: str
    signal_type: str

    location_name: str
    target_date: str
    variable_name: str

    model_value: float | None = None
    model_band: str | None = None
    market_band: str | None = None

    edge_direction: str | None = None
    edge_strength: float | None = None

    confidence: Confidence
    action_hint: str

    notes: list[str] = []
