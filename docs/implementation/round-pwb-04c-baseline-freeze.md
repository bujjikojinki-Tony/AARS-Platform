# Round_PWB-04C_Baseline_Freeze

## 1. Freeze Decision
Round PWB-04C - Test Isolation & App Factory Hardening is frozen.

Status:
```text
ACCEPTED BASELINE
```

## 2. Freeze Scope

The accepted baseline includes:
- `backend/services.py`
- `backend/app_factory.py`
- thin `backend/main.py`
- router injection through `create_app()`
- isolated SQLite-backed FastAPI instances
- API tests migrated to `create_app()`
- PWB-04C isolation regression tests

## 3. Stable Rules

- `create_app(db_path, allow_network=False)` returns a FastAPI app.
- `/healthz` reports `mode`, `db_path`, `allow_network`, and `live_execution = false`.
- `allow_network` defaults to `false`.
- `default_year` defaults to `2026`.
- `default_sigma` defaults to `2.5`.
- `LIVE_EXECUTE` remains rejected.
- scanning in one app does not affect another app.

## 4. Stable Router Set

The frozen app factory includes:
- opportunities router
- command router
- history router
- settings router
- weather router
- evidence router
- workstation router
- probability governance router

## 5. Safety Boundary

This freeze does not add:
- new probability logic
- new trading logic
- real Polymarket access
- real DEB/EMOS
- live execution
- frontend changes

## 6. Freeze Rule

Only defects required to preserve PWB-04C isolation and router integration acceptance may be fixed after this note.
No new feature work belongs in PWB-04C after freeze.
