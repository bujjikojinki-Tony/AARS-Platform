from __future__ import annotations

from pydantic import BaseModel, Field


class MarketRule(BaseModel):
    market_id: str
    market_question: str
    market_type: str = Field(description="e.g. daily_high_temperature")
    location_name: str
    target_date: str | None = None
    station_name: str | None = None
    nws_station_id: str | None = None
    cdo_station_id: str | None = None
    variable_name: str = Field(description="e.g. daily_max_temperature")
    timezone: str
    source_name: str
    raw_rules_text: str
    parse_confidence: float = 0.0
    needs_review: bool = True
