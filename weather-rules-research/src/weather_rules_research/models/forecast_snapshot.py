from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ForecastSnapshot(BaseModel):
    location_name: str
    forecast_issued_at: datetime
    target_date: str
    variable_name: str
    value: float
    source: str
