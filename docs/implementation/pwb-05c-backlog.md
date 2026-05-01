# PWB-05C Backlog

Status: Draft
Date: 2026-05-01
Scope: Shadow Engine Evaluation Matrix v0

## Objective
Build a read-only historical evaluation matrix for the accepted primary and shadow engines while remaining non-executing and non-promoting.

PWB-05C answers:

```text
How do we compare Gaussian, DEB shadow, and EMOS shadow behavior over accepted historical memory without changing the active engine or introducing execution or promotion behavior?
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
- No retraining

## Round Boundary
This round is shadow evaluation and comparison only.

It must preserve:

- calibration memory integrity
- DEB shadow integrity
- EMOS shadow integrity
- active engine stability
- read-only visibility

It must not introduce:

- new execution behavior
- new scan behavior
- new simulation behavior
- automatic promotion behavior

## Execution Order

### 1. Models and SQLite Foundation
Create comparison-row and summary models first.

Deliverables:
- evaluation models under `backend/models/`
- SQLite tables for comparison rows and summaries
- indexes on market, engine, and timestamp fields

Acceptance:
- Models serialize cleanly
- `init_db()` creates the new evaluation tables
- Existing schema initialization remains intact

### 2. Repository Methods
Add repository helpers for saving and querying comparison rows.

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
- Comparison rows can be saved and queried
- Summary returns counts and rankings

### 3. Read-Only Evaluation Service
Add a dedicated service for assembling comparison rows from accepted memory and shadow outputs.

Deliverables:
- per-market comparison computation
- aggregate summary generation
- summary and lookup methods

Rules:
- Service must not call `StrategyRunner`
- Service must not call `Simulator`
- Service must not call execution
- Service must not change the active engine
- Service must not call promotion gates

Acceptance:
- Service computes deterministic comparison outputs from existing memory
- Service persists evaluation rows cleanly

### 4. Read-Only APIs
Expose evaluation visibility and manual build entrypoints.

Planned routes:
- summary endpoint
- recent comparison rows endpoint
- market evaluation bundle endpoint
- manual build endpoint using existing memory only

Rules:
- APIs remain read-only from an execution perspective
- APIs do not drive execution or promotion
- APIs do not modify the active engine

Acceptance:
- Evaluation summary works
- Market evaluation lookup works
- Manual build works

### 5. Dashboard Surface
Expose shadow evaluation visibility in the existing dashboard shell.

Important note:
- This workspace uses the `weather-dashboard` Streamlit shell, not a React `frontend/` app

Planned panel behavior:
- show evaluation summary
- show recent comparison rows
- allow market evaluation lookup
- allow manual build for testing

Forbidden UI:
- Trade
- Execute
- Simulate
- Promote Model
- Go Live

Acceptance:
- History shell can inspect evaluation state
- UI stays read-only and non-executing

### 6. Verification
Add focused acceptance coverage for models, storage, service, APIs, and safety boundaries.

Planned test file:
- `tests/test_pwb05c_shadow_engine_evaluation_matrix.py`

Acceptance targets:
- model serialization
- evaluation tables created
- repository save/list/summary
- matrix build from accepted memory
- read-only API behavior
- active engine unchanged
- promotion not triggered
- `LIVE_EXECUTE` still rejected

### 7. Freeze
Freeze the round once model, storage, service, API, dashboard surface, and acceptance tests are green.

Freeze must state:
- PWB-05C is a read-only shadow evaluation round
- It does not change the active engine
- It does not trigger strategy, simulation, execution, or promotion side effects

## Stop Condition
Stop once shadow comparison results can be computed from accepted historical memory, queried safely, and surfaced without changing active engine behavior or execution behavior.
