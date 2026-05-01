# Round_PWB-05_Status_Note

## 1. Round
Round PWB-05 — Real Calibration Data & Backtest Memory v0

## 2. Status
Accepted for baseline freeze.

## 3. Purpose
PWB-05 assembles existing archived records into reusable historical sample memory.

It combines:

- market snapshot archive
- weather archive
- probability engine run
- outcome resolution

It persists:

- calibration samples
- backtest memory records

It does not:

- run the probability engine
- run strategy
- run simulation
- execute
- promote models
- trade

## 4. Accepted Capabilities

- `CalibrationSample`
- `BacktestMemoryRecord`
- eligibility checks
- read-only sample builders
- read-only calibration memory APIs
- dashboard shell calibration memory panel

## 5. Accepted API Surface

- `GET /api/calibration-memory/summary`
- `GET /api/calibration-memory/samples`
- `GET /api/calibration-memory/backtests`
- `GET /api/calibration-memory/market/{market_id}`
- `GET /api/calibration-memory/eligibility/{market_id}`
- `POST /api/calibration-memory/build-sample`
- `POST /api/calibration-memory/build-backtest`
- `POST /api/calibration-memory/build-all-eligible`

## 6. Safety Boundary

PWB-05 is sample/memory only and non-executing.

It must not trigger:

- probability engine execution
- `StrategyRunner`
- candidate generation
- simulation
- execution
- promotion

`LIVE_EXECUTE` remains rejected.
