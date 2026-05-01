# Round_PWB-05A_Accepted_Path_Inventory

## Accepted Backend Paths

- `backend/models/deb_shadow.py`
- `backend/deb_shadow/deb_shadow_service.py`
- `backend/api/routes_deb_shadow.py`
- `backend/storage/db.py`
- `backend/storage/repositories.py`
- `backend/app_factory.py`

## Accepted Dashboard Shell Paths

- `weather-dashboard/src/weather_dashboard/types/weather.py`
- `weather-dashboard/src/weather_dashboard/ui/deb_shadow_panel.py`
- `weather-dashboard/src/weather_dashboard/ui/r5_pages.py`

## Accepted Tests

- `tests/test_pwb05a_real_deb_shadow.py`
- `weather-dashboard/tests/test_deb_shadow_panel.py`

## Accepted Boundary

The accepted PWB-05A implementation computes and stores DEB shadow results from accepted historical memory only.

It does not:

- change the active engine
- run engines as active policy
- run strategy
- create candidates
- simulate
- execute
- promote
- trade
