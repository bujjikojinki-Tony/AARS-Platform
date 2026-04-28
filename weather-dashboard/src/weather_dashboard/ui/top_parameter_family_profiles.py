from __future__ import annotations


FAMILY_TOP_PARAMETER_PROFILES: dict[str, dict[str, str]] = {
    "temperature_daily_max": {
        "observation_label": "Obs Temp",
        "forecast_label": "Fcst Temp",
        "unit": "°C",
    },
    "temperature_daily_min": {
        "observation_label": "Obs Temp",
        "forecast_label": "Fcst Temp",
        "unit": "°C",
    },
    "precipitation_amount": {
        "observation_label": "Obs Rain",
        "forecast_label": "Fcst Rain",
        "unit": "mm",
    },
    "wind_speed": {
        "observation_label": "Obs Wind",
        "forecast_label": "Fcst Wind",
        "unit": "kt",
    },
    "sea_ice_extent": {
        "observation_label": "Latest Extent",
        "forecast_label": "Projected Extent",
        "unit": "M km²",
    },
    "global_temperature_index": {
        "observation_label": "Latest Index",
        "forecast_label": "Projected Index",
        "unit": "index",
    },
}


def get_family_top_parameter_profile(market_family: str | None) -> dict[str, str]:
    family = str(market_family or "").strip().lower()
    return FAMILY_TOP_PARAMETER_PROFILES.get(
        family,
        {
            "observation_label": "Observation",
            "forecast_label": "Forecast",
            "unit": "-",
        },
    )
