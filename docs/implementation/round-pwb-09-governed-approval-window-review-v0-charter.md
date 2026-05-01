# Round_PWB-09_Governed_Approval_Window_Review_v0_Charter

## 1. Round Position
Round PWB-09 builds on the accepted PWB-08 governed execution-queue review baseline and the architecture's Layer 6 governance & execution layer.

PWB-08 answered:

```text
How can the system present a governed execution queue review from accepted historical evidence without introducing execution, simulation, or trading side effects?
```

PWB-09 answers:

```text
How can the system present governed approval-window review context from accepted historical evidence without introducing execution, simulation, or trading side effects?
```

## 2. Purpose
The goal of PWB-09 is to add a read-only approval-window review layer for operator-facing governance.

This round should establish:

- approval-window review records
- approval pending / approved / rejected visibility
- read-only approval summaries and bundles
- read-only APIs for approval-window visibility
- dashboard shell visibility for approval-window state

## 3. Scope
PWB-09 includes:

- approval-window review models
- SQLite tables and indexes for approval review records
- repository methods
- read-only approval-window review service
- read-only approval-window review APIs
- dashboard visibility in the current shell
- acceptance tests
- freeze docs

## 4. Non-Goals
PWB-09 does not add:

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
PWB-09 is review-only.

It may read:

- execution queue review rows
- execution decision review rows
- command review rows
- shadow evaluation rows
- calibration memory rows
- outcome resolution rows

It may produce:

- approval-window review rows
- approval summaries
- operator-facing approval bundles

It must not:

- change the active probability engine
- re-run strategy
- generate candidates
- execute trades
- invoke promotion gates

## 6. Safety Boundary
PWB-09 must remain read-only and non-executing.

Governed approval-window review behavior must not trigger:

- `StrategyRunner`
- `Simulator`
- execution
- trading
- promotion

It may only compute and persist approval-review context.

## 7. Expected Outputs
This round should produce:

- `docs/implementation/pwb-09-backlog.md`
- later architecture and governance notes
- later freeze docs once accepted

## 8. Next Step
Translate this charter into an executable backlog before implementing models, storage, or APIs.
