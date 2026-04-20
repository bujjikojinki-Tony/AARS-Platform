from weather_rules_research.config import get_settings
from weather_rules_research.models import Station
from weather_rules_research.official_obs import OfficialObservationFetcher
from weather_rules_research.open_meteo import OpenMeteoForecastClient


def test_get_settings_reads_environment_variables(monkeypatch) -> None:
    monkeypatch.setenv("OPEN_METEO_BASE_URL", "https://example-open-meteo.test")
    monkeypatch.setenv("NOAA_BASE_URL", "https://example-noaa.test")
    monkeypatch.setenv("NWS_BASE_URL", "https://example-nws.test")

    settings = get_settings()

    assert settings.open_meteo_base_url == "https://example-open-meteo.test"
    assert settings.noaa_base_url == "https://example-noaa.test"
    assert settings.nws_base_url == "https://example-nws.test"


def test_clients_use_configured_base_urls(monkeypatch) -> None:
    monkeypatch.setenv("OPEN_METEO_BASE_URL", "https://example-open-meteo.test")
    monkeypatch.setenv("NOAA_BASE_URL", "https://example-noaa.test")
    monkeypatch.setenv("NWS_BASE_URL", "https://example-nws.test")

    forecast_client = OpenMeteoForecastClient()
    obs_client = OfficialObservationFetcher()
    station = Station(
        station_name="Phoenix Sky Harbor International Airport",
        nws_station_id="KPHX",
        cdo_station_id="GHCND:USW00023183",
        latitude=33.4,
        longitude=-112.0,
        source="manual_whitelist",
    )

    assert forecast_client.build_forecast_url(station).startswith(
        "https://example-open-meteo.test/v1/forecast"
    )
    assert obs_client.build_daily_summaries_url("KPHX").startswith(
        "https://example-noaa.test/access/services/data/v1"
    )
    assert obs_client.build_station_points_url(33.4, -112.0) == (
        "https://example-nws.test/points/33.4,-112.0"
    )
