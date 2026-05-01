# PWB-04G Backlog

Status: Draft
Date: 2026-04-30
Scope: Outcome Resolver Read-Only v0

## Objective
Build a passive, read-only outcome-resolution layer that preserves market outcome state and source metadata for later calibration and backtest preparation.

PWB-04G answers:

```text
How do we record market outcome-resolution facts without introducing settlement execution or trading side effects?
```

## Non-Goals
- No trading
- No wallet integration
- No signing
- No order placement
- No order cancellation
- No live execution
- No automatic settlement execution
- No automatic calibration
- No automatic model promotion
- No DEB
- No EMOS
- No backtest engine

## Round Boundary
This round is read-only outcome resolution only.

It must preserve:

- market outcome state
- outcome source metadata
- outcome timestamps
- alignment-friendly resolution facts

It must not introduce:

- new execution behavior
- new scan behavior
- new simulation behavior
- new promotion behavior

## Execution Order

### 1. Models and SQLite Foundation
Create outcome-resolution models and storage tables first so later service and API work has a stable persistence layer.

Deliverables:
- outcome resolver models under `backend/models/`
- outcome-resolution SQLite tables
- indexes on market, status, and observed-at/resolved-at fields

Acceptance:
- Models serialize cleanly
- `init_db()` creates the new resolver tables
- Existing schema initialization remains intact

### 2. Repository Resolver Methods
Add repository helpers for outcome-resolution persistence and lookup.

Deliverables:
- save methods for outcome-resolution rows
- latest-by-market query
- recent list query
- summary query

Rules:
- Repository stays CRUD-only
- No strategy
- No simulation
- No execution

Acceptance:
- Outcome-resolution rows can be saved and queried
- Summary returns counts and distributions

### 3. Read-Only Resolver Service
Add a dedicated service for passive resolution recording and readback.

Deliverables:
- read-only outcome resolver service
- helper methods for manual record save
- helper methods for listing and summarizing records

Rules:
- Service must not call `StrategyRunner`
- Service must not call `Simulator`
- Service must not call `Execution`
- Service must not trigger settlement behavior

Acceptance:
- Service can persist manual resolution records
- Service can return latest resolution record by market

### 4. Read-Only Resolver APIs
Expose outcome-resolution visibility and manual resolution entrypoints.

Planned routes:
- summary endpoint
- recent resolution endpoint
- market resolution endpoint
- manual resolution write endpoint

Rules:
- APIs remain read-only with respect to trading
- APIs do not drive settlement execution
- APIs do not change execution mode

Acceptance:
- Resolution summary works
- Market lookup works
- Manual resolution record write works

### 5. Dashboard Surface
Expose read-only outcome-resolution visibility in the existing dashboard shell.

Important note:
- This workspace uses the `weather-dashboard` Streamlit shell, not a React `frontend/` app

Planned panel behavior:
- show resolution summary
- show recent resolution records
- allow market resolution lookup
- allow manual resolution archive for testing

Forbidden UI:
- Trade
- Execute
- Simulate
- Settle Position
- Go Live

Acceptance:
- History and/or Settings shell can inspect resolver state
- UI stays read-only and non-executing

### 6. Verification
Add focused acceptance coverage for resolver models, storage, APIs, and safety boundaries.

Planned test file:
- `tests/test_pwb04g_outcome_resolver_read_only.py`

Acceptance targets:
- resolver model serialization
- resolver tables created
- manual resolution save
- recent resolution list
- latest-by-market query
- summary query
- read-only resolver API behavior
- `LIVE_EXECUTE` still rejected

### 7. Freeze
Freeze the round once model, storage, service, API, dashboard surface, and acceptance tests are green.

Freeze must state:
- PWB-04G is a read-only outcome resolver round
- It does not settle trades
- It does not trigger execution, calibration, or promotion side effects

## Stop Condition
Stop once outcome-resolution records can be persisted, queried, and surfaced safely, with explicit proof that resolver behavior remains read-only and `LIVE_EXECUTE` is still rejected.
