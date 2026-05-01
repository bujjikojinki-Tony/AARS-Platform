# Round_PWB-11_Governed_Activation_Authorization_Review_v0_Charter

## 1. Round Position
Round PWB-11 builds on the accepted PWB-10 governed activation-readiness review baseline and the architecture's Layer 6 governance & execution layer.

PWB-10 answered:

```text
How can the system present governed activation-readiness review context from accepted historical evidence without introducing execution, simulation, or trading side effects?
```

PWB-11 answers:

```text
How can the system present governed activation-authorization review context from accepted historical evidence without introducing execution, simulation, or trading side effects?
```

## 2. Purpose
The goal of PWB-11 is to add a read-only activation-authorization review layer for operator-facing governance.

This round should establish:

- activation-authorization review records
- authorization state visibility derived from prior governed review layers
- read-only authorization summaries and bundles
- read-only APIs for activation-authorization visibility
- dashboard shell visibility for activation-authorization state

## 3. Scope
PWB-11 includes:

- activation-authorization review models
- SQLite tables and indexes for authorization review records
- repository methods
- read-only activation-authorization review service
- read-only activation-authorization review APIs
- dashboard visibility in the current shell
- acceptance tests
- freeze docs

## 4. Non-Goals
PWB-11 does not add:

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
PWB-11 is review-only.

It may read:

- activation-readiness review rows
- approval-window review rows
- execution queue review rows
- execution decision review rows
- command review rows
- shadow evaluation rows
- calibration memory rows
- outcome resolution rows

It may produce:

- activation-authorization review rows
- authorization summaries
- operator-facing authorization bundles

It must not:

- change the active probability engine
- re-run strategy
- generate candidates
- execute trades
- invoke promotion gates

## 6. Safety Boundary
PWB-11 must remain read-only and non-executing.

Governed activation-authorization review behavior must not trigger:

- `StrategyRunner`
- `Simulator`
- execution
- trading
- promotion

It may only compute and persist activation-authorization review context.

## 7. Expected Outputs
This round should produce:

- `docs/implementation/pwb-11-backlog.md`
- later architecture and governance notes
- later freeze docs once accepted

## 8. Next Step
Translate this charter into an executable backlog before implementing models, storage, or APIs.
