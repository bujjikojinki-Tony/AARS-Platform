# Round_PWB-07_Governed_Execution_Decision_Review_v0_Charter

## 1. Round Position
Round PWB-07 builds on the accepted PWB-06 governed command review baseline and the architecture's Layer 6 governance & execution layer.

PWB-06 answered:

```text
How can the system present governed command review and approval context from accepted historical evidence without introducing execution, simulation, or promotion side effects?
```

PWB-07 answers:

```text
How can the system present governed execution-decision review context from accepted historical evidence without introducing execution, simulation, or trading side effects?
```

## 2. Purpose
The goal of PWB-07 is to add a read-only execution-decision review layer for operator-facing governance.

This round should establish:

- execution-decision review records
- mode, gate, and approval context
- read-only execution review summaries and bundles
- read-only APIs for execution-decision visibility
- dashboard shell visibility for execution-decision state

## 3. Scope
PWB-07 includes:

- execution-decision review models
- SQLite tables and indexes for decision review records
- repository methods
- read-only execution-decision review service
- read-only execution-decision review APIs
- dashboard visibility in the current shell
- acceptance tests
- freeze docs

## 4. Non-Goals
PWB-07 does not add:

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
PWB-07 is review-only.

It may read:

- accepted market snapshots
- weather forecasts
- weather actuals
- outcomes
- calibration memory
- shadow evaluation rows
- command review rows

It may produce:

- execution-decision review rows
- mode and gate summaries
- operator-facing decision bundles

It must not:

- change the active probability engine
- re-run strategy
- generate candidates
- execute trades
- invoke promotion gates

## 6. Safety Boundary
PWB-07 must remain read-only and non-executing.

Governed execution-decision review behavior must not trigger:

- `StrategyRunner`
- `Simulator`
- execution
- trading
- promotion

It may only compute and persist decision-review context.

## 7. Expected Outputs
This round should produce:

- `docs/implementation/pwb-07-backlog.md`
- later architecture and governance notes
- later freeze docs once accepted

## 8. Next Step
Translate this charter into an executable backlog before implementing models, storage, or APIs.
