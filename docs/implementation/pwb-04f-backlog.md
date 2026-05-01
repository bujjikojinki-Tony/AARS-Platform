# PWB-04F Backlog

Status: Draft
Date: 2026-04-30
Scope: Weather Forecast Archive v0

## Objective
Build a passive, time-indexed weather archive layer that preserves the weather-side inputs used by the existing PWB-02 and PWB-03 flows.

PWB-04F answers:

```text
What forecast inputs, evidence, thresholds, directions, and weather views did the system observe when it built a weather probability?
```

## Non-Goals
- No trading
- No wallet integration
- No signing
- No order placement
- No order cancellation
- No live execution
- No auto calibration
- No automatic model promotion
- No outcome resolver
- No real DEB
- No real EMOS
- No backtest engine

## Round Boundary
This round is weather-side archival only.

It must preserve:

- forecast input state
- evidence-pack state
- weather-view state

It must not introduce:

- new execution behavior
- new scan behavior
- new simulation behavior
- new model-governance behavior

## Execution Order

### 1. Models and SQLite Foundation
Create weather-archive models and storage tables first so later service and API work has a stable persistence layer.

Deliverables:
- `backend/models/weather_archive.py`
- `WeatherForecastArchiveRecord`
- `WeatherEvidenceArchiveRecord`
- `WeatherViewArchiveRecord`
- `WeatherArchiveSummary`
- `weather_forecast_archive`
- `weather_evidence_archive`
- `weather_view_archive`
- recommended indexes on market, weather-view, evidence-pack, and archived-at columns

Acceptance:
- Archive models serialize cleanly
- `init_db()` creates all three archive tables
- Existing schema initialization remains intact

### 2. Repository Archive Methods
Add persistence helpers for weather-side archive data.

Deliverables:
- save methods for forecast, evidence, and weather-view archive rows
- recent list methods for each archive family
- summary query
- market bundle query by `market_id`
- row parsers for JSON fields

Rules:
- Repository stays CRUD-only
- No weather fetches
- No strategy behavior
- No simulation
- No execution

Acceptance:
- Forecast/evidence/view rows can be saved and read back
- Summary returns counts and distributions
- A market bundle can return all archived weather-side rows for one market

### 3. Weather Archive Service
Add a dedicated archive service that converts runtime weather-side objects into persisted archive rows.

Deliverables:
- `backend/archive/weather_forecast_archive_service.py`
- `archive_weather_view(...)`
- `archive_evidence_pack(...)`
- `archive_forecast_record(...)`
- recent-query helpers
- market-bundle helper
- summary helper

Expected inputs:
- `WeatherView`
- evidence-pack-like payloads
- source metadata and forecast observation values

Accepted archive reasons:
- `WEATHER_VIEW_CAPTURE`
- `PROBABILITY_BUILD_CAPTURE`
- `MANUAL_CAPTURE`
- `SCAN_CAPTURE`

Acceptance:
- Weather view archive works
- Evidence pack archive works
- Forecast record archive works

### 4. Passive Capture Hooks
Attach archive writes only to already-existing weather-side flows.

Accepted hook points:
- `WeatherProbabilityProvider.build_probability_view(...)`
- weather-side API entrypoints such as `/api/weather/probability` or `/api/weather/resolve`
- post-scan passive capture after weather-side objects already exist
- manual archive APIs

Rules:
- Archive failure must not fail the main probability or scan path
- Archive hooks must not change candidate count
- Archive hooks must not trigger simulation or execution
- Archive hooks must not fetch extra market data

Acceptance:
- Probability build may archive weather-side records without changing output semantics
- Optional archive flags work without changing existing safe defaults

### 5. Weather Archive APIs
Expose read-only archive visibility and manual archive entrypoints.

Planned routes:
- `GET /api/weather-archive/summary`
- `GET /api/weather-archive/views`
- `GET /api/weather-archive/forecasts`
- `GET /api/weather-archive/evidence`
- `GET /api/weather-archive/market/{market_id}`
- `POST /api/weather-archive/view`
- `POST /api/weather-archive/forecast`
- `POST /api/weather-archive/evidence`
- `POST /api/weather-archive/latest/{market_id}`

Rules:
- `latest/{market_id}` archives already-available weather-side data only
- No weather fetch is triggered by the archive-only endpoint
- No strategy, simulation, or execution is triggered

Acceptance:
- Summary works
- Recent list endpoints work
- Market bundle endpoint works
- Manual archive endpoints work
- Latest-weather archive endpoint works and remains passive

### 6. UI Surface
Expose weather archive visibility in the existing dashboard shell.

Important note:
- This workspace uses the `weather-dashboard` Streamlit shell, not a React `frontend/` app

Planned panel behavior:
- show weather archive summary
- show recent weather views
- show recent forecasts
- show recent evidence packs
- allow archive-latest action for a market
- allow market weather archive bundle lookup

Forbidden UI:
- Trade
- Execute
- Simulate
- Backtest Now
- Promote Model
- Auto Calibrate
- Go Live

Acceptance:
- History and/or Evidence surface can inspect weather archive state
- UI stays read-only and non-executing

### 7. Verification
Add focused acceptance coverage for archive models, storage, APIs, and passive behavior.

Planned test file:
- `tests/test_pwb04f_weather_forecast_archive.py`

Acceptance targets:
- weather archive models serialize
- weather archive tables are created
- archive weather view record
- archive evidence record
- archive forecast record
- weather archive summary
- weather archive market bundle
- weather archive latest API
- weather archive latest does not create candidates
- optional probability-build archive path
- weather archive UI/API path
- `LIVE_EXECUTE` still rejected

### 8. Freeze
Freeze the round once model, storage, service, passive capture hooks, APIs, dashboard surface, and acceptance tests are green.

Freeze must state:
- PWB-04F is a read-only weather archive round
- It archives weather-side evidence only
- It does not create trading, execution, or model-promotion side effects

## Stop Condition
Stop once weather forecast, evidence, and weather-view archive records can be persisted, queried, and surfaced safely, with explicit proof that archive behavior remains passive and `LIVE_EXECUTE` is still rejected.
