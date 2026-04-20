from pydantic import BaseModel


class Rule(BaseModel):
    market_id: str
    market_question: str
    market_type: str
    location_name: str
    target_date: str | None = None

    station_name: str | None = None
    nws_station_id: str | None = None
    cdo_station_id: str | None = None

    variable_name: str
    timezone: str
    source_name: str

    parse_confidence: float = 0.0
    needs_review: bool = True
