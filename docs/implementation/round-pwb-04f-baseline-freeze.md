# Round_PWB-04F_Baseline_Freeze

## 1. Freeze Decision
Round PWB-04F - Weather Forecast Archive v0 is frozen.

Status:
```text
ACCEPTED BASELINE
```

## 2. Freeze Scope

The accepted baseline includes:
- weather archive models
- weather archive SQLite tables
- weather archive repository methods
- weather archive service
- weather archive APIs
- archive-latest passive path
- optional probability-build archive hook
- dashboard weather archive panel
- PWB-04F acceptance tests

## 3. Stable Architecture

Accepted PWB-04F architecture:

```text
WeatherSourceRecord / EvidencePack / WeatherView
  -> WeatherForecastArchiveService
  -> WeatherForecastArchiveRecord / WeatherEvidenceArchiveRecord / WeatherViewArchiveRecord
  -> weather_*_archive tables
```

## 4. Stable API Boundary

Accepted APIs may save and read weather archive records only.

They must not:
- fetch external weather
- run strategy
- create candidates
- simulate
- execute
- trade
- calibrate
- promote models

## 5. Stable Safety Boundary

The following remain frozen:
- `LIVE_EXECUTE` remains rejected
- no wallet
- no signing
- no order placement
- no order cancellation
- no live execution

PWB-04F additionally freezes:
- weather archive is passive
- weather archive must not drive action
- weather archive must not become calibration, backtest, or promotion behavior
- dashboard weather archive visibility must remain read-only and non-executing

## 6. Baseline Acceptance Criteria

PWB-04F baseline is accepted if:
1. weather archive tables exist
2. repository can save and query weather archive records
3. archive service can archive weather views, evidence packs, and forecast records
4. summary and market bundle work
5. archive-latest archives existing latest weather-side records only
6. archive-latest does not create candidates
7. archive-latest does not fetch weather
8. probability-build archive optional path works
9. scan candidate count is unchanged
10. dashboard History shell can inspect weather archive without trade/execute controls
11. `LIVE_EXECUTE` remains rejected

## 7. No Further Expansion Rule

After this freeze:
- do not add external weather fetches to archive APIs
- do not add strategy, simulation, or execution behavior to PWB-04F
- do not add calibration, backtest, or model-promotion logic to PWB-04F

## 8. Freeze Statement

PWB-04F is frozen as the first accepted Weather Forecast Archive baseline.
It persists time-indexed weather-side records for later calibration and backtest preparation.
It does not generate signals, candidates, simulations, executions, trades, calibration results, or promotion decisions.
Archive-latest reads existing latest weather-side records and archives them only.
LIVE_EXECUTE remains rejected.
