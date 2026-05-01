# Round_PWB-06_Status_Note

## 1. Round
Round PWB-06 — Governed Command Review v0

## 2. Status
Accepted for baseline freeze.

## 3. Purpose
PWB-06 adds a read-only command review layer for the governed action console.

It assembles already accepted historical records into reviewable command context, including:

- market snapshot archive
- weather archive
- outcome resolution
- calibration memory
- DEB shadow
- EMOS shadow
- shadow engine evaluation

PWB-06 does not:

- run strategy
- generate candidates
- simulate
- execute
- promote models
- trade

## 4. Accepted Capabilities

- `CommandReviewRecord`
- `CommandReviewSummary`
- `CommandReviewBundle`
- read-only command review repository helpers
- read-only command review service
- read-only command review APIs
- dashboard shell governed command review panel

## 5. Accepted API Surface

- `GET /api/command-review/summary`
- `GET /api/command-review/reviews`
- `GET /api/command-review/market/{market_id}`
- `POST /api/command-review/build`
- `POST /api/command-review/build-all`

## 6. Safety Boundary

PWB-06 is review-only and non-executing.

It must not trigger:

- `StrategyRunner`
- `Simulator`
- execution
- promotion
- trading

`LIVE_EXECUTE` remains rejected.
