# Round_PWB-04G_Status_Note

## 1. Round
Round PWB-04G — Outcome Resolver Read-Only v0

## 2. Status
Accepted for baseline freeze.

## 3. Purpose
PWB-04G adds a read-only and manual outcome-resolution layer.

It records:

- market outcome state
- weather actual observations
- resolution records derived from actuals plus threshold/direction context

It does not:

- call strategy
- simulate
- execute
- calibrate
- promote models
- trade

## 4. Accepted Capabilities

- `MarketOutcomeRecord`
- `WeatherActualRecord`
- `OutcomeResolutionRecord`
- `OutcomeBundle`
- `OutcomeArchiveSummary`
- read-only outcome resolver service
- read-only outcome APIs
- dashboard shell outcome panel

## 5. Accepted API Surface

- `GET /api/outcomes/summary`
- `GET /api/outcomes/markets`
- `GET /api/outcomes/weather-actuals`
- `GET /api/outcomes/resolutions`
- `GET /api/outcomes/market/{market_id}`
- `POST /api/outcomes/market`
- `POST /api/outcomes/weather-actual`
- `POST /api/outcomes/resolve-from-weather`

## 6. Safety Boundary

PWB-04G is read-only/manual and non-executing.

It must not trigger:

- `StrategyRunner`
- `Simulator`
- execution
- calibration
- model promotion
- trading

`LIVE_EXECUTE` remains rejected.
