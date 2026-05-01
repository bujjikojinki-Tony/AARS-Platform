# Round_PWB-05_Real_Calibration_Data_And_Backtest_Memory_v0_Charter

## 1. Round Position
Round PWB-05 builds on the accepted archive and resolver rounds:

- PWB-04E Market Snapshot Archive
- PWB-04F Weather Forecast Archive
- PWB-04G Outcome Resolver Read-Only

PWB-05 answers:

```text
How can the system combine archived market inputs, weather inputs, probability runs, and resolved outcomes into real calibration-ready and backtest-ready memory records without introducing live execution behavior?
```

## 2. Purpose
The goal of PWB-05 is to create a first accepted baseline for real calibration data and backtest memory.

This round should establish:

- calibration sample models
- backtest memory models
- SQLite storage for assembled historical samples
- repository and service helpers for sample assembly
- read-only APIs for querying assembled memory
- visibility in the current dashboard shell

## 3. Scope
PWB-05 includes:

- sample-assembly data models
- SQLite tables and indexes for calibration memory and backtest memory
- repository methods
- read-only assembly service
- read-only APIs
- dashboard visibility for sample memory
- acceptance tests
- freeze docs

## 4. Non-Goals
PWB-05 does not add:

- live trading
- wallet integration
- signing
- order placement
- order cancellation
- automatic execution
- real DEB implementation
- real EMOS implementation
- auto model promotion

## 5. Core Idea
PWB-05 does not invent new forecasts or outcomes.

It only assembles already accepted records into reusable historical memory:

```text
MarketSnapshotArchiveRecord
+ WeatherForecastArchiveRecord / WeatherViewArchiveRecord
+ ProbabilityEngineRun / ProbabilityComparison
+ OutcomeResolutionRecord
= CalibrationSample / BacktestMemoryRecord
```

## 6. Safety Boundary
PWB-05 must remain read-only and non-executing.

Assembly behavior must not trigger:

- `StrategyRunner`
- `Simulator`
- execution
- trading
- order placement
- automatic promotion

It may only read existing records and persist assembled memory.

## 7. Expected Outputs
This round should produce:

- `docs/implementation/pwb-05-backlog.md`
- later architecture and governance notes
- later freeze docs once accepted

## 8. Next Step
Translate this charter into an executable backlog before implementing models, storage, or APIs.
