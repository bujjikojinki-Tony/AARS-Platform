# Round_PWB-04F_Accepted_Path_Inventory

## 1. Purpose
This document freezes the accepted files and implementation paths for:

```text
Round PWB-04F - Weather Forecast Archive v0
```

## 2. Accepted Backend Model Files

- `backend/models/weather_archive.py`

Accepted objects:
- `WeatherForecastArchiveRecord`
- `WeatherEvidenceArchiveRecord`
- `WeatherViewArchiveRecord`
- `WeatherArchiveSummary`
- `WeatherArchiveBundle`

Accepted enums:
- `WeatherArchiveReason`
- `WeatherForecastSourceType`
- `WeatherArchiveMetric`
- `WeatherArchiveUnit`

## 3. Accepted Storage Extensions

Accepted tables:
- `weather_forecast_archive`
- `weather_evidence_archive`
- `weather_view_archive`

Accepted storage file:
- `backend/storage/db.py`

## 4. Accepted Repository Methods

Accepted repository file:
- `backend/storage/repositories.py`

Accepted methods:
- `save_weather_forecast_archive_record`
- `save_weather_evidence_archive_record`
- `save_weather_view_archive_record`
- `list_weather_forecast_archive`
- `list_weather_evidence_archive`
- `list_weather_view_archive`
- `get_weather_archive_bundle`
- `get_weather_archive_summary`

Accepted boundary:
- repository persists and queries archive data only
- repository does not fetch weather, run strategy, simulate, execute, calibrate, or promote

## 5. Accepted Archive Service

Accepted file:
- `backend/archive/weather_forecast_archive_service.py`

Accepted class:
- `WeatherForecastArchiveService`

Accepted methods:
- `archive_weather_view`
- `archive_evidence_pack`
- `archive_forecast_record`
- `archive_probability_build_bundle`
- `archive_existing_latest_market_bundle`

## 6. Accepted Weather Archive API

Accepted file:
- `backend/api/routes_weather_archive.py`

Accepted endpoints:
- `GET /api/weather-archive/summary`
- `GET /api/weather-archive/views`
- `GET /api/weather-archive/forecasts`
- `GET /api/weather-archive/evidence`
- `GET /api/weather-archive/market/{market_id}`
- `POST /api/weather-archive/view`
- `POST /api/weather-archive/forecast`
- `POST /api/weather-archive/evidence`
- `POST /api/weather-archive/latest/{market_id}`

Accepted endpoint boundary:
- archive APIs persist and read weather-side archive records only
- archive APIs do not fetch external weather
- archive APIs do not call `StrategyRunner`
- archive APIs do not simulate or execute

## 7. Accepted Probability-Build Hook

Accepted files:
- `backend/probability/weather_probability_provider.py`
- `backend/services.py`
- `backend/app_factory.py`
- `backend/api/routes_weather.py`

Accepted flag:
- `archive_weather_on_probability_build`

Accepted behavior:
- normal probability build semantics stay unchanged
- after `WeatherView` is saved, weather archive persistence may run as a passive sidecar
- archive failure must not fail the probability build path

## 8. Accepted Dashboard Shell

Accepted dashboard files:
- `weather-dashboard/src/weather_dashboard/types/weather.py`
- `weather-dashboard/src/weather_dashboard/ui/weather_forecast_archive_panel.py`
- `weather-dashboard/src/weather_dashboard/ui/r5_pages.py`

Accepted dashboard behavior:
- show weather archive summary
- show recent forecasts
- show recent evidence
- show recent weather views
- allow market bundle lookup
- allow archive latest weather view

Forbidden dashboard behavior:
- trade
- execute
- auto calibrate
- promote model
- wallet
- order
- cancel
- go live

## 9. Accepted Tests

Accepted test file:
- `tests/test_pwb04f_weather_forecast_archive.py`
- `weather-dashboard/tests/test_weather_forecast_archive_panel.py`

Accepted test groups:
- weather archive table creation
- archive service summary and bundle
- archive latest passive safety
- optional probability-build archive path
- scan candidate-count stability
- weather archive API shapes
- dashboard weather archive panel state and row-mapping
- `LIVE_EXECUTE` rejection

## 10. Accepted Runtime Defaults

- `allow_network = false`
- `allow_polymarket_network = false`
- `market_source_mode = MOCK_ONLY`
- `live_execution = false`
- `archive_weather_on_probability_build = false`

## 11. Inventory Status

PWB-04F accepted path inventory is complete.
