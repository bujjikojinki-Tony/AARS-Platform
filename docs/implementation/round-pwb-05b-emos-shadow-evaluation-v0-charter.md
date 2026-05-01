# Round_PWB-05B_EMOS_Shadow_Evaluation_v0_Charter

## 1. Round Position
Round PWB-05B builds on the accepted PWB-05 calibration-memory baseline and the accepted PWB-05A DEB shadow baseline.

PWB-05 answered:

```text
How can the system assemble archived market, weather, probability, and outcome records into reusable historical sample memory without introducing execution behavior?
```

PWB-05A answered:

```text
How can the system use real historical sample memory to produce a Dynamic Error Balancing shadow probability stream without changing the active engine or introducing trading side effects?
```

PWB-05B answers:

```text
How can the system evaluate an EMOS-style shadow probability stream from accepted historical memory without changing the active engine or introducing execution, calibration, or promotion side effects?
```

## 2. Purpose
The goal of PWB-05B is to add the first real EMOS shadow evaluation layer on top of accepted historical sample memory.

This round should establish:

- EMOS shadow inputs from accepted calibration memory
- read-only EMOS-style shadow computations
- persistence for EMOS shadow runs and diagnostics
- read-only APIs for EMOS shadow visibility
- dashboard shell visibility for EMOS shadow results

## 3. Scope
PWB-05B includes:

- EMOS shadow data models
- SQLite tables and indexes for EMOS shadow runs
- repository methods
- read-only EMOS shadow service
- read-only EMOS shadow APIs
- dashboard visibility in the current shell
- acceptance tests
- freeze docs

## 4. Non-Goals
PWB-05B does not add:

- active-engine switching
- live trading
- wallet integration
- signing
- order placement
- order cancellation
- automatic execution
- automatic model promotion
- real ensemble ingestion
- real calibration retraining

## 5. Core Idea
PWB-05B is shadow-only.

It may read:

- calibration samples
- backtest memory
- archived weather inputs
- archived outcome facts

It may produce:

- EMOS-adjusted shadow probabilities
- EMOS diagnostics and fit metadata

It must not:

- change the active probability engine
- re-run strategy
- generate candidates
- execute trades

## 6. Safety Boundary
PWB-05B must remain read-only and non-executing.

EMOS shadow behavior must not trigger:

- `StrategyRunner`
- `Simulator`
- execution
- trading
- promotion

It may only compute and persist shadow results.

## 7. Expected Outputs
This round should produce:

- `docs/implementation/pwb-05b-backlog.md`
- later architecture and governance notes
- later freeze docs once accepted

## 8. Next Step
Translate this charter into an executable backlog before implementing models, storage, or APIs.
