# Round_PWB-04G_Outcome_Resolver_Read_Only_v0_Charter

## 1. Round Position
Round PWB-04G adds a read-only outcome-resolution layer on top of the accepted PWB-04E market archive and accepted PWB-04F weather archive.

PWB-04E answered:

```text
What market state did the system observe at a given time?
```

PWB-04F answered:

```text
What weather-side forecast, evidence, and weather-view inputs did the system observe at that same time?
```

PWB-04G answers:

```text
How can the system record outcome-resolution state for a market without introducing execution, trading, or auto-settlement behavior?
```

## 2. Purpose
The goal of PWB-04G is to add a read-only outcome resolver baseline that can preserve market-resolution state, resolution-source metadata, and operator-supplied or externally-read resolution results without introducing live trading, settlement execution, or automatic strategy changes.

This round should establish:

- outcome-resolution record models
- read-only resolution storage
- repository and service helpers
- read-only resolution APIs
- visibility in the existing dashboard shell

## 3. Scope
PWB-04G includes:

- outcome resolver models
- SQLite tables and indexes for resolution history
- repository methods
- read-only outcome resolver service
- read-only outcome resolver APIs
- visibility in the current dashboard shell
- acceptance tests
- freeze docs

## 4. Non-Goals
PWB-04G does not add:

- live execution
- trading
- wallet integration
- signing
- order placement
- order cancellation
- automatic settlement execution
- automatic model promotion
- automatic calibration computation
- DEB
- EMOS
- backtest engine

## 5. Core Idea
PWB-04G is not a full settlement engine.

It is a read-only resolver layer that captures:

- what market outcome state is known
- what source the outcome came from
- when it was observed
- how it aligns to archived market and weather-side evidence

## 6. Safety Boundary
PWB-04G must remain read-only and non-executing.

Resolver behavior must not trigger:

- `StrategyRunner`
- `Simulator`
- `Execution`
- trading
- automatic model promotion

It may only persist and expose outcome-resolution facts.

## 7. Relationship to Later Rounds
PWB-04G is a prerequisite for later calibration and backtest memory work because it adds the outcome-side record needed to complete a historical sample.

Target future alignment:

```text
MarketSnapshotArchiveRecord
+ WeatherForecastArchiveRecord
+ WeatherViewArchiveRecord
+ ProbabilityEngineRun
+ OutcomeResolverRecord
= CalibrationSample / BacktestMemoryRecord
```

PWB-04G does not build those samples yet.

## 8. Expected Outputs
This round should produce:

- `docs/implementation/pwb-04g-backlog.md`
- `docs/architecture/outcome-resolver-read-only-v0.md`
- `docs/governance/outcome-resolver-safety-rules-v0.md`
- later freeze docs once accepted

## 9. Next Step
Translate this charter into an executable backlog before implementing models, storage, or APIs.
