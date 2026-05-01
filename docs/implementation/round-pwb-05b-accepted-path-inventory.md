# Round_PWB-05B_Accepted_Path_Inventory

## Accepted Backend Paths

- `backend/models/emos_shadow.py`
- `backend/emos_shadow/emos_shadow_service.py`
- `backend/api/routes_emos_shadow.py`
- `backend/storage/db.py`
- `backend/storage/repositories.py`
- `backend/app_factory.py`

## Accepted Dashboard Shell Paths

- `weather-dashboard/src/weather_dashboard/types/weather.py`
- `weather-dashboard/src/weather_dashboard/ui/emos_shadow_panel.py`
- `weather-dashboard/src/weather_dashboard/ui/r5_pages.py`

## Accepted Tests

- `tests/test_pwb05b_emos_shadow.py`
- `weather-dashboard/tests/test_emos_shadow_panel.py`

## Accepted Boundary

The accepted PWB-05B implementation computes and stores EMOS shadow results from accepted historical memory only.

It does not:

- change the active engine
- run engines as active policy
- run strategy
- create candidates
- simulate
- execute
- promote
- trade
