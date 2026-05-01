# Round_PWB-04C_Accepted_Path_Inventory

## 1. Purpose
This document freezes the accepted implementation paths for:

```text
Round PWB-04C - Test Isolation & App Factory Hardening
```

## 2. Accepted Backend Files

- `backend/services.py`
- `backend/app_factory.py`
- `backend/main.py`

Accepted responsibilities:

| File | Responsibility |
| --- | --- |
| `backend/services.py` | Build `AppServices` and shared runtime objects |
| `backend/app_factory.py` | Create isolated FastAPI apps from a database path |
| `backend/main.py` | Create the default app via `create_app(DEFAULT_DB_PATH, allow_network=False)` |

## 3. Accepted Router Integration

Accepted routers mounted by `create_app()`:
- `backend/api/routes_opportunities.py`
- `backend/api/routes_command.py`
- `backend/api/routes_history.py`
- `backend/api/routes_settings.py`
- `backend/api/routes_weather.py`
- `backend/api/routes_evidence.py`
- `backend/api/routes_workstation.py`
- `backend/api/routes_probability_governance.py`

Accepted router behavior:
- all routers use the same `AppServices.repository` instance within one app
- router paths remain unchanged

## 4. Accepted Test Paths

- `tests/test_pwb04c_app_factory_isolation.py`
- PWB-02 API tests using `create_app()`
- PWB-03 API tests using `create_app()`

Accepted test rules:
- use `tmp_path` SQLite databases
- do not import `backend.main.app` in API tests
- verify app instance isolation

## 5. Accepted Runtime Defaults

```text
allow_network = false
default_year = 2026
default_sigma = 2.5
live_execution = false
```

## 6. Not Accepted Paths

- new trading logic
- real Polymarket connector
- real DEB or EMOS implementations
- frontend modifications
- live execution enablement

## 7. Inventory Status

PWB-04C accepted path inventory is complete.
