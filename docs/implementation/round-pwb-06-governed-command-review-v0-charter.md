# Round_PWB-06_Governed_Command_Review_v0_Charter

## 1. Round Position
Round PWB-06 builds on the accepted PWB-05C shadow evaluation baseline and the architecture's governed action console layer.

PWB-05C answered:

```text
How can the system compare accepted primary and shadow probability streams on the same historical memory and persist a read-only evaluation matrix without changing active-engine behavior or triggering promotion?
```

PWB-06 answers:

```text
How can the system present governed command review and approval context from accepted historical evidence without introducing execution, simulation, or promotion side effects?
```

## 2. Purpose
The goal of PWB-06 is to add a read-only command review layer for operator-facing governance.

This round should establish:

- governed command review records
- approval context and decision metadata
- read-only review summaries and bundles
- read-only APIs for command visibility
- dashboard shell visibility for command review state

## 3. Scope
PWB-06 includes:

- command review models
- SQLite tables and indexes for command review records
- repository methods
- read-only command review service
- read-only command review APIs
- dashboard visibility in the current shell
- acceptance tests
- freeze docs

## 4. Non-Goals
PWB-06 does not add:

- live trading
- wallet integration
- signing
- order placement
- order cancellation
- automatic execution
- automatic promotion
- simulation-driven actioning
- retraining
- recalibration reruns

## 5. Core Idea
PWB-06 is review-only.

It may read:

- accepted market snapshots
- weather forecasts
- weather actuals
- outcomes
- calibration memory
- shadow evaluation rows

It may produce:

- command review rows
- approval context summaries
- operator-facing recommendation bundles

It must not:

- change the active probability engine
- re-run strategy
- generate candidates
- execute trades
- invoke promotion gates

## 6. Safety Boundary
PWB-06 must remain read-only and non-executing.

Governed command review behavior must not trigger:

- `StrategyRunner`
- `Simulator`
- execution
- trading
- promotion

It may only compute and persist review context.

## 7. Expected Outputs
This round should produce:

- `docs/implementation/pwb-06-backlog.md`
- later architecture and governance notes
- later freeze docs once accepted

## 8. Next Step
Translate this charter into an executable backlog before implementing models, storage, or APIs.
