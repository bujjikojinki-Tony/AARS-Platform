# PWB-05 Backlog

Status: Draft
Date: 2026-04-30
Scope: Real Calibration Data & Backtest Memory v0

## Objective
Assemble real historical calibration-ready and backtest-ready memory records from already accepted archive and resolver layers.

PWB-05 answers:

```text
How do we turn archived market/weather inputs plus probability runs and resolved outcomes into reusable historical samples without introducing execution behavior?
```

## Non-Goals
- No live trading
- No wallet integration
- No signing
- No order placement
- No order cancellation
- No live execution
- No automatic strategy changes
- No real DEB
- No real EMOS
- No auto promotion

## Round Boundary
This round is read-only sample assembly only.

It must preserve:

- existing archive integrity
- outcome resolver integrity
- calibration-ready historical alignment
- backtest-memory persistence

It must not introduce:

- new execution behavior
- new scan behavior
- new simulation behavior
- new promotion behavior

## Execution Order

### 1. Models and SQLite Foundation
Create calibration-sample and backtest-memory models and tables first.

Deliverables:
- calibration memory models under `backend/models/`
- backtest memory tables
- indexes on market, engine, and sample timestamp fields

Acceptance:
- Models serialize cleanly
- `init_db()` creates the new memory tables
- Existing schema initialization remains intact

### 2. Repository Methods
Add repository helpers for saving and querying assembled memory records.

Deliverables:
- save methods
- recent list queries
- market bundle queries
- summary queries

Rules:
- Repository stays CRUD-only
- No strategy
- No simulation
- No execution

Acceptance:
- Memory rows can be saved and queried
- Summary returns counts and distributions

### 3. Read-Only Assembly Service
Add a dedicated service for building memory records from accepted archives.

Deliverables:
- calibration sample assembly helpers
- backtest memory assembly helpers
- summary and lookup methods

Rules:
- Service must not call `StrategyRunner`
- Service must not call `Simulator`
- Service must not call execution
- Service must only consume existing records

Acceptance:
- Service can assemble memory from existing market/weather/outcome records
- Service returns deterministic assembled records

### 4. Read-Only APIs
Expose assembled memory through read-only APIs.

Planned routes:
- summary endpoint
- recent calibration sample endpoint
- recent backtest memory endpoint
- market memory bundle endpoint
- manual assembly endpoint using existing record ids only

Rules:
- APIs remain read-only with respect to trading
- APIs do not drive execution or promotion
- APIs do not create new forecast/outcome facts

Acceptance:
- Memory summary works
- Market memory lookup works
- Manual read-only assembly works

### 5. Dashboard Surface
Expose read-only calibration memory and backtest memory in the existing dashboard shell.

Important note:
- This workspace uses the `weather-dashboard` Streamlit shell, not a React `frontend/` app

Planned panel behavior:
- show memory summary
- show recent calibration samples
- show recent backtest memory records
- allow market memory lookup
- allow manual assembly from existing ids for testing

Forbidden UI:
- Trade
- Execute
- Simulate
- Backtest Now
- Go Live

Acceptance:
- History shell can inspect memory state
- UI stays read-only and non-executing

### 6. Verification
Add focused acceptance coverage for models, storage, service, APIs, and safety boundaries.

Planned test file:
- `tests/test_pwb05_real_calibration_memory.py`

Acceptance targets:
- model serialization
- memory tables created
- repository save/list/summary
- sample assembly from existing archive records
- read-only API behavior
- `LIVE_EXECUTE` still rejected

### 7. Freeze
Freeze the round once model, storage, service, API, dashboard surface, and acceptance tests are green.

Freeze must state:
- PWB-05 is a read-only historical memory round
- It does not execute trades
- It does not trigger strategy, simulation, or promotion side effects

## Stop Condition
Stop once calibration-ready and backtest-ready memory records can be assembled from existing accepted layers, queried safely, and surfaced without changing execution behavior.
