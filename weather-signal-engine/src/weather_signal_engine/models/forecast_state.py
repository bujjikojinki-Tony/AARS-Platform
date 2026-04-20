from pydantic import BaseModel


class ForecastState(BaseModel):
    location_name: str
    target_date: str
    variable_name: str

    latest_forecast_value: float
    source_mode: str
    forecast_issued_at: str | None = None

    run_to_run_delta: float | None = None
    model_band: str | None = None
