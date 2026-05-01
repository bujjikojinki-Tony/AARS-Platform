# PWB-01 Backend Skeleton v0

This directory contains a standalone `Polymarket Bot` backend skeleton for **Round PWB-01**.

Current scope:
- mock market source only
- placeholder probability only
- SQLite persistence
- strategy runner
- risk gate
- simulator
- FastAPI endpoints
- audit logging

Out of scope:
- real Polymarket connectivity
- real weather intelligence
- live trading
- frontend
- PWB-02 and beyond

## Directory Layout

```text
polymarket-bot/
  backend/
    main.py
    models/
    storage/
    sources/
    probability/
    strategies/
    execution/
    governance/
    api/
  tests/
    test_pwb01_acceptance.py
  requirements.txt
```

## Requirements

Install dependencies with:

```bash
python -m pip install -r requirements.txt
```

Note:
- In this workspace, `python -m pytest` is the reliable way to run tests.
- Plain `pytest` may resolve to a different interpreter that does not have `fastapi` installed.

## Start the Backend

From `/Users/maolei/AARS-Platform/polymarket-bot`:

```bash
uvicorn backend.main:app --reload
```

Default runtime behavior:
- database file: `pwb01.sqlite`
- execution mode: `OBSERVE_ONLY`
- live execution: disabled

## Health Check

```bash
curl http://127.0.0.1:8000/healthz
```

Expected response shape:

```json
{
  "status": "ok",
  "mode": "OBSERVE_ONLY",
  "live_execution": false
}
```

## Main API Flows

### 1. Scan mock markets

```bash
curl -X POST http://127.0.0.1:8000/api/opportunities/scan
```

This will:
- fetch mock markets
- run strategies
- create signals
- create candidates
- apply risk gate
- persist audit logs

### 2. List candidates

```bash
curl http://127.0.0.1:8000/api/opportunities
```

### 3. Get one candidate

```bash
curl http://127.0.0.1:8000/api/opportunities/<candidate_id>
```

### 4. Block one candidate

```bash
curl -X POST http://127.0.0.1:8000/api/opportunities/<candidate_id>/block
```

## Command API

### Run scan

```bash
curl -X POST http://127.0.0.1:8000/api/command \
  -H "Content-Type: application/json" \
  -d '{"command":"/run scan"}'
```

### Simulate one candidate

```bash
curl -X POST http://127.0.0.1:8000/api/command \
  -H "Content-Type: application/json" \
  -d '{"command":"/simulate <candidate_id>"}'
```

### Show rules

```bash
curl -X POST http://127.0.0.1:8000/api/command \
  -H "Content-Type: application/json" \
  -d '{"command":"/show rules"}'
```

### Set safe mode

```bash
curl -X POST http://127.0.0.1:8000/api/command \
  -H "Content-Type: application/json" \
  -d '{"command":"/set mode simulation"}'
```

Supported command patterns:
- `/run scan`
- `/list opportunities`
- `/simulate <candidate_id>`
- `/block <candidate_id>`
- `/set mode simulation`
- `/set mode observe_only`
- `/show rules`
- `/show history`

Rejected / unsupported:
- live trading commands
- auto-trade commands

## History Endpoints

Signals:

```bash
curl http://127.0.0.1:8000/api/history/signals
```

Candidates:

```bash
curl http://127.0.0.1:8000/api/history/candidates
```

Simulations:

```bash
curl http://127.0.0.1:8000/api/history/simulations
```

Audit logs:

```bash
curl http://127.0.0.1:8000/api/history/audit
```

## Settings Endpoints

Get rules:

```bash
curl http://127.0.0.1:8000/api/settings/rules
```

Update rules:

```bash
curl -X POST http://127.0.0.1:8000/api/settings/rules \
  -H "Content-Type: application/json" \
  -d '{"min_edge_percent":12,"min_liquidity":150,"max_spread":0.07}'
```

Get mode:

```bash
curl http://127.0.0.1:8000/api/settings/mode
```

Set mode:

```bash
curl -X POST http://127.0.0.1:8000/api/settings/mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"SIMULATION"}'
```

Safety boundary:
- `LIVE_EXECUTE` is rejected in PWB-01

## Run Acceptance Tests

From `/Users/maolei/AARS-Platform/polymarket-bot`:

```bash
python -m pytest tests/test_pwb01_acceptance.py -q
```

Current acceptance tests cover:
- scan creates candidates
- risk gate blocks weak candidates
- simulation does not trade live
- mode defaults to `OBSERVE_ONLY`
- command execution is audited

## Data and State

Default SQLite file:

```text
polymarket-bot/pwb01.sqlite
```

Tables:
- `market_snapshots`
- `strategy_signals`
- `opportunity_candidates`
- `execution_decisions`
- `simulation_results`
- `audit_logs`
- `rule_configs`
- `system_state`

## Safety Boundaries

This skeleton is intentionally constrained:
- mock data only
- no real exchange integration
- no real weather ingestion
- no live execution path
- no portfolio management

`Simulator` only produces `SimulationResult` and audit events.

## Known Notes

- The backend is intentionally minimal and deterministic.
- This is a backend skeleton for PWB-01 only.
- PWB-02 should extend this through new modules rather than weakening the current safety boundary.
