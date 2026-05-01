# Round_PWB-04C_Status_Note

## 1. Round
Round PWB-04C - Test Isolation & App Factory Hardening

## 2. Status
Accepted for baseline freeze.

## 3. Purpose
PWB-04C is an engineering hardening round. It does not change trading logic, probability logic, or model governance.

Its purpose is to:
- isolate FastAPI app instances by database path
- keep PWB-01, PWB-02, and PWB-03 routers mounted through `create_app()`
- preserve the existing API surface without depending on `backend.main.app` in tests

## 4. Accepted Scope

Accepted PWB-04C chain:
```text
create_services()
  -> AppServices
  -> create_app(db_path, allow_network=False, default_year=2026, default_sigma=2.5)
  -> router injection
  -> isolated SQLite-backed FastAPI app
```

## 5. Accepted Behavior

- `/healthz` returns `mode`, `db_path`, `allow_network`, and `live_execution = false`.
- `create_app()` returns a FastAPI app instance.
- The same `AppServices.repository` is shared across all routers in one app.
- Weather router receives `allow_network`, `default_year`, and `default_sigma` from `create_app()`.
- Existing API paths remain unchanged.
- `LIVE_EXECUTE` remains rejected.

## 6. Not Accepted

PWB-04C does not introduce:
- real Polymarket connector
- real DEB
- real EMOS
- new trading behavior
- live execution
- frontend changes

## 7. Freeze Boundary

Only defects required to preserve PWB-04C isolation acceptance may be fixed after this note.
No new features belong to PWB-04C after freeze.
