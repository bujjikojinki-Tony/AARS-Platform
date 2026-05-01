# Round_PWB-05A_Status_Note

## 1. Round
Round PWB-05A — Real DEB Shadow Implementation v0

## 2. Status
Accepted for baseline freeze.

## 3. Purpose
PWB-05A computes and persists DEB shadow outputs from accepted historical calibration memory.

It consumes:

- calibration samples
- backtest memory context

It persists:

- DEB shadow runs
- DEB shadow diagnostics

It does not:

- change the active engine
- run strategy
- create candidates
- simulate
- execute
- promote models
- trade

## 4. Accepted Capabilities

- `DebShadowRunRecord`
- `DebShadowDiagnosticRecord`
- read-only DEB shadow repository helpers
- `DebShadowService`
- read-only DEB shadow APIs
- dashboard shell DEB shadow panel

## 5. Accepted API Surface

- `GET /api/deb-shadow/summary`
- `GET /api/deb-shadow/runs`
- `GET /api/deb-shadow/diagnostics`
- `GET /api/deb-shadow/market/{market_id}`
- `POST /api/deb-shadow/build`
- `POST /api/deb-shadow/build-all`

## 6. Safety Boundary

PWB-05A is shadow-only and non-executing.

It must not trigger:

- probability engine execution
- `StrategyRunner`
- candidate generation
- simulation
- execution
- promotion

The active engine remains unchanged.
`LIVE_EXECUTE` remains rejected.
