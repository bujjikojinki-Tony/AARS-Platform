# PWB-05B Backlog

Status: Draft
Date: 2026-05-01
Scope: EMOS Shadow Evaluation v0

## Objective
Build a real EMOS-style shadow probability evaluation layer that consumes accepted historical memory while remaining shadow-only and non-executing.

PWB-05B answers:

```text
How do we compute and persist an EMOS-style shadow probability stream from real historical sample memory without changing the active engine or introducing execution behavior?
```

## Non-Goals
- No active-engine switching
- No live trading
- No wallet integration
- No signing
- No order placement
- No order cancellation
- No live execution
- No automatic strategy changes
- No auto promotion
- No real ensemble ingestion

## Round Boundary
This round is EMOS shadow computation only.

It must preserve:

- calibration memory integrity
- backtest memory integrity
- active engine stability
- shadow-only visibility

It must not introduce:

- new execution behavior
- new scan behavior
- new simulation behavior
- automatic promotion behavior

## Execution Order

### 1. Models and SQLite Foundation
Create EMOS shadow run and diagnostic models first.

Deliverables:
- EMOS shadow models under `backend/models/`
- SQLite tables for shadow runs and diagnostics
- indexes on market, engine, and run timestamp fields

Acceptance:
- Models serialize cleanly
- `init_db()` creates the new EMOS shadow tables
- Existing schema initialization remains intact

### 2. Repository Methods
Add repository helpers for saving and querying EMOS shadow rows.

Deliverables:
- save methods
- recent list queries
- market lookup queries
- summary queries

Rules:
- Repository stays CRUD-only
- No strategy
- No simulation
- No execution

Acceptance:
- Shadow rows can be saved and queried
- Summary returns counts and distributions

### 3. Read-Only EMOS Shadow Service
Add a dedicated service for computing EMOS-style shadow outputs from accepted memory.

Deliverables:
- EMOS shadow probability computation
- diagnostic metadata generation
- summary and lookup methods

Rules:
- Service must not call `StrategyRunner`
- Service must not call `Simulator`
- Service must not call execution
- Service must not change the active engine

Acceptance:
- Service computes deterministic shadow outputs from existing memory
- Service persists shadow results cleanly

### 4. Read-Only APIs
Expose EMOS shadow visibility and manual build entrypoints.

Planned routes:
- summary endpoint
- recent shadow runs endpoint
- market shadow bundle endpoint
- manual shadow build endpoint using existing memory only

Rules:
- APIs remain shadow-only
- APIs do not drive execution or promotion
- APIs do not modify the active engine

Acceptance:
- Shadow summary works
- Market shadow lookup works
- Manual shadow build works

### 5. Dashboard Surface
Expose EMOS shadow visibility in the existing dashboard shell.

Important note:
- This workspace uses the `weather-dashboard` Streamlit shell, not a React `frontend/` app

Planned panel behavior:
- show shadow summary
- show recent EMOS shadow runs
- allow market shadow lookup
- allow manual shadow build for testing

Forbidden UI:
- Trade
- Execute
- Simulate
- Promote Model
- Go Live

Acceptance:
- History shell can inspect EMOS shadow state
- UI stays shadow-only and non-executing

### 6. Verification
Add focused acceptance coverage for models, storage, service, APIs, and safety boundaries.

Planned test file:
- `tests/test_pwb05b_emos_shadow.py`

Acceptance targets:
- model serialization
- EMOS tables created
- repository save/list/summary
- shadow build from accepted memory
- read-only API behavior
- active engine unchanged
- `LIVE_EXECUTE` still rejected

### 7. Freeze
Freeze the round once model, storage, service, API, dashboard surface, and acceptance tests are green.

Freeze must state:
- PWB-05B is a real EMOS shadow round
- It does not change the active engine
- It does not trigger strategy, simulation, execution, or promotion side effects

## Stop Condition
Stop once EMOS shadow results can be computed from accepted historical memory, queried safely, and surfaced without changing active engine behavior or execution behavior.
