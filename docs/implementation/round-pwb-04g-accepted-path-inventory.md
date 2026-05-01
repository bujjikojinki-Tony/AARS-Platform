# Round_PWB-04G_Accepted_Path_Inventory

## Accepted Backend Paths

- `backend/models/outcome.py`
- `backend/outcome/outcome_resolver_read_only_service.py`
- `backend/api/routes_outcomes.py`
- `backend/storage/db.py`
- `backend/storage/repositories.py`
- `backend/app_factory.py`

## Accepted Dashboard Shell Paths

- `weather-dashboard/src/weather_dashboard/types/weather.py`
- `weather-dashboard/src/weather_dashboard/ui/outcome_resolver_panel.py`
- `weather-dashboard/src/weather_dashboard/ui/r5_pages.py`

## Accepted Tests

- `tests/test_pwb04g_outcome_resolver_read_only.py`

## Accepted Boundary

The accepted PWB-04G implementation stores and exposes outcome facts only.

It does not:

- fetch external outcome state automatically
- run strategy
- simulate
- execute
- calibrate
- promote
- trade
