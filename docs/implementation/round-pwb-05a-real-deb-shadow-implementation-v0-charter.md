# Round_PWB-05A_Real_DEB_Shadow_Implementation_v0_Charter

## 1. Round Position
Round PWB-05A builds on the accepted PWB-05 calibration and backtest memory baseline.

PWB-05 answered:

```text
How can the system assemble archived market, weather, probability, and outcome records into reusable historical sample memory without introducing execution behavior?
```

PWB-05A answers:

```text
How can the system use real historical sample memory to produce a Dynamic Error Balancing shadow probability stream without changing the active engine or introducing trading side effects?
```

## 2. Purpose
The goal of PWB-05A is to add the first real DEB shadow implementation on top of accepted historical samples.

This round should establish:

- DEB shadow model inputs from accepted calibration memory
- read-only DEB shadow computations
- persistence for DEB shadow runs and diagnostics
- read-only APIs for DEB shadow visibility
- dashboard shell visibility for DEB shadow results

## 3. Scope
PWB-05A includes:

- DEB shadow data models
- SQLite tables and indexes for DEB shadow runs
- repository methods
- read-only DEB shadow service
- read-only DEB shadow APIs
- dashboard visibility in the current shell
- acceptance tests
- freeze docs

## 4. Non-Goals
PWB-05A does not add:

- active-engine switching
- live trading
- wallet integration
- signing
- order placement
- order cancellation
- automatic execution
- EMOS
- automatic model promotion

## 5. Core Idea
PWB-05A is shadow-only.

It may read:

- calibration samples
- backtest memory
- archived weather inputs
- archived outcome facts

It may produce:

- DEB-adjusted shadow probabilities
- DEB diagnostics and error-balancing metadata

It must not:

- change the active probability engine
- re-run strategy
- generate candidates
- execute trades

## 6. Safety Boundary
PWB-05A must remain read-only and non-executing.

DEB shadow behavior must not trigger:

- `StrategyRunner`
- `Simulator`
- execution
- trading
- promotion

It may only compute and persist shadow results.

## 7. Expected Outputs
This round should produce:

- `docs/implementation/pwb-05a-backlog.md`
- later architecture and governance notes
- later freeze docs once accepted

## 8. Next Step
Translate this charter into an executable backlog before implementing models, storage, or APIs.
