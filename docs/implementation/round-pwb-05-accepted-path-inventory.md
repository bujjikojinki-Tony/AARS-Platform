# Round_PWB-05_Accepted_Path_Inventory

## Accepted Backend Paths

- `backend/models/calibration_memory.py`
- `backend/calibration_memory/calibration_sample_builder.py`
- `backend/calibration_memory/backtest_memory_builder.py`
- `backend/api/routes_calibration_memory.py`
- `backend/storage/db.py`
- `backend/storage/repositories.py`
- `backend/app_factory.py`

## Accepted Dashboard Shell Paths

- `weather-dashboard/src/weather_dashboard/types/weather.py`
- `weather-dashboard/src/weather_dashboard/ui/calibration_memory_panel.py`
- `weather-dashboard/src/weather_dashboard/ui/r5_pages.py`

## Accepted Tests

- `tests/test_pwb05_calibration_memory.py`

## Accepted Boundary

The accepted PWB-05 implementation assembles and stores historical sample memory only.

It does not:

- run engines
- run strategy
- create candidates
- simulate
- execute
- promote
- trade
