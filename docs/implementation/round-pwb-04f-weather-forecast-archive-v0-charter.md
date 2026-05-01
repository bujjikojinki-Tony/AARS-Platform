# Round_PWB-04F_Weather_Forecast_Archive_v0_Charter

## 1. Round Position
Round PWB-04F adds a read-only weather-side archive layer on top of the accepted PWB-02 weather intelligence flow and the accepted PWB-04E market snapshot archive.

PWB-04E answered:

```text
What market state did the system observe at a given time?
```

PWB-04F answers:

```text
What weather forecast inputs, evidence, thresholds, directions, and weather views did the system observe at that same time?
```

## 2. Purpose
The goal of PWB-04F is to persist the weather-side inputs that were previously transient runtime objects:

- `WeatherDescriptor`
- `EvidencePack`
- `WeatherView`
- forecast-source observations used by the probability flow

This round creates a time-indexed `WeatherForecastArchive` layer so later rounds can align weather-side evidence with market-side archive records for calibration, audit, and backtest preparation.

## 3. Scope
PWB-04F includes:

- weather archive models
- weather archive SQLite tables and indexes
- repository archive methods
- weather archive service
- optional passive archive hooks from weather probability / weather APIs / scan
- weather archive APIs
- weather archive visibility in the existing dashboard shell
- acceptance tests
- freeze documents

## 4. Non-Goals
PWB-04F does not add:

- outcome resolver behavior
- real calibration engine behavior
- backtest engine behavior
- DEB
- EMOS
- model training
- automatic promotion
- trading
- wallet integration
- signing
- order placement
- order cancellation
- live execution

## 5. Core Objects
PWB-04F introduces:

- `WeatherForecastArchiveRecord`
- `WeatherEvidenceArchiveRecord`
- `WeatherViewArchiveRecord`
- `WeatherArchiveSummary`

These objects preserve the weather-side evidence chain that led to a probability build.

## 6. Core Capture Paths
Accepted capture paths for this round:

- probability-build capture
- weather API capture
- post-scan capture
- manual archive capture

All capture paths are passive archive paths only.

## 7. Safety Boundary
PWB-04F must remain read-only and non-executing.

Archive behavior must not trigger:

- `StrategyRunner`
- `Simulator`
- `Execution`
- `PromotionGate`

Archive behavior may only persist already-available weather-side records or weather views produced by an existing accepted flow.

## 8. Relationship to Later Rounds
PWB-04F is a prerequisite for later historical calibration and backtest memory work.

Target future alignment:

```text
MarketSnapshotArchiveRecord
+ WeatherForecastArchiveRecord
+ WeatherViewArchiveRecord
+ ProbabilityEngineRun
+ MarketOutcome
= CalibrationSample
```

PWB-04F does not build that calibration sample yet. It only preserves the weather-side inputs required for that later work.

## 9. Expected Outputs
This round should produce:

- `docs/implementation/pwb-04f-backlog.md`
- `docs/architecture/weather-forecast-archive-v0.md`
- `docs/governance/weather-archive-safety-rules-v0.md`
- later freeze docs once the implementation is accepted

## 10. Next Step
Translate this charter into an executable backlog before starting model, schema, or API work.
