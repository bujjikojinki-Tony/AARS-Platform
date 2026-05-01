# Round_PWB-05C_Shadow_Engine_Evaluation_Matrix_v0_Charter

## 1. Round Position
Round PWB-05C builds on the accepted PWB-05 calibration-memory baseline, the accepted PWB-05A DEB shadow baseline, and the accepted PWB-05B EMOS shadow baseline.

PWB-05 answered:

```text
How can the system assemble archived market, weather, probability, and outcome records into reusable historical sample memory without introducing execution behavior?
```

PWB-05A answered:

```text
How can the system use real historical sample memory to produce a Dynamic Error Balancing shadow probability stream without changing the active engine or introducing trading side effects?
```

PWB-05B answered:

```text
How can the system evaluate an EMOS-style shadow probability stream from accepted historical memory without changing the active engine or introducing execution, calibration, or promotion side effects?
```

PWB-05C answers:

```text
How can the system compare accepted primary and shadow probability streams on the same historical memory and persist a read-only evaluation matrix without changing active-engine behavior or triggering promotion?
```

## 2. Purpose
The goal of PWB-05C is to add a read-only evaluation layer that compares Gaussian, DEB shadow, and EMOS shadow outputs over accepted historical memory.

This round should establish:

- engine-to-engine historical comparison records
- read-only comparison summaries and rankings
- persisted evaluation matrix rows
- read-only APIs for comparison visibility
- dashboard shell visibility for shadow evaluation state

## 3. Scope
PWB-05C includes:

- shadow engine evaluation models
- SQLite tables and indexes for evaluation matrix rows
- repository methods
- read-only evaluation service
- read-only evaluation APIs
- dashboard visibility in the current shell
- acceptance tests
- freeze docs

## 4. Non-Goals
PWB-05C does not add:

- active-engine switching
- live trading
- wallet integration
- signing
- order placement
- order cancellation
- automatic execution
- automatic promotion
- retraining
- recalibration reruns

## 5. Core Idea
PWB-05C is comparison-only.

It may read:

- calibration samples
- DEB shadow runs
- EMOS shadow runs
- primary engine probability records

It may produce:

- per-market comparison rows
- aggregate scorecards
- read-only ranking summaries

It must not:

- change the active probability engine
- re-run strategy
- generate candidates
- execute trades
- invoke promotion gates

## 6. Safety Boundary
PWB-05C must remain read-only and non-executing.

Shadow evaluation behavior must not trigger:

- `StrategyRunner`
- `Simulator`
- execution
- trading
- promotion

It may only compute and persist comparison results.

## 7. Expected Outputs
This round should produce:

- `docs/implementation/pwb-05c-backlog.md`
- later architecture and governance notes
- later freeze docs once accepted

## 8. Next Step
Translate this charter into an executable backlog before implementing models, storage, or APIs.
