# Round_PWB-06_Accepted_Path_Inventory

## Accepted Backend Paths

- `backend/models/command_review.py`
- `backend/storage/db.py`
- `backend/storage/repositories.py`
- `backend/command_review/command_review_service.py`
- `backend/api/routes_command_review.py`
- `backend/app_factory.py`

## Accepted Dashboard Shell Paths

- `weather-dashboard/src/weather_dashboard/types/weather.py`
- `weather-dashboard/src/weather_dashboard/ui/command_review_panel.py`
- `weather-dashboard/src/weather_dashboard/ui/r5_pages.py`

## Accepted Tests

- `tests/test_pwb06_command_review.py`
- `weather-dashboard/tests/test_command_review_panel.py`

## Accepted Boundary

The accepted PWB-06 implementation assembles and displays governed command review context only.

It does not:

- run strategy
- create candidates
- simulate
- execute
- promote
- trade
