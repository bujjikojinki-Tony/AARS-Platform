# Round_PWB-05C_Accepted_Path_Inventory

## Accepted Backend Paths

- `backend/models/shadow_engine_evaluation.py`
- `backend/shadow_engine_evaluation/shadow_engine_evaluation_service.py`
- `backend/api/routes_shadow_engine_evaluation.py`
- `backend/storage/db.py`
- `backend/storage/repositories.py`
- `backend/app_factory.py`

## Accepted Dashboard Shell Paths

- `weather-dashboard/src/weather_dashboard/types/weather.py`
- `weather-dashboard/src/weather_dashboard/ui/shadow_engine_evaluation_panel.py`
- `weather-dashboard/src/weather_dashboard/ui/r5_pages.py`

## Accepted Tests

- `tests/test_pwb05c_shadow_engine_evaluation_matrix.py`
- `weather-dashboard/tests/test_shadow_engine_evaluation_panel.py`

## Accepted Boundary

The accepted PWB-05C implementation computes and stores read-only cross-engine comparison results from accepted historical memory only.

It does not:

- change the active engine
- run engines as active policy
- run strategy
- create candidates
- simulate
- execute
- promote
- trade
