# MIL-3.30 Frozen Forward Evidence Accumulation and Drift Monitoring

MIL-3.30 automatically recognizes newly completed weekly post-freeze folds,
archives one immutable checkpoint per fold and re-runs the unchanged MIL-3.29
gate. It never searches parameters, edits the frozen specification, creates a
proposal, activates a configuration or connects to an order path.

## Collection contract

Checkpoint zero is evaluated exactly at the source snapshot's freeze boundary.
It is the state/cost drift reference. Each later checkpoint is evaluated at the
final fully closed candle of one canonical post-freeze fold. Scheduler delay
does not move that boundary: missed weeks are reconstructed and archived in
order, up to a bounded per-cycle limit.

Each record binds:

- frozen specification SHA-256;
- immutable source v2 snapshot;
- exact synchronized validation boundary;
- post-freeze fold count;
- complete MIL-3.29 report SHA-256;
- permanent PAPER_ONLY authority locks.

`(spec_sha256, post_freeze_fold_count)` is unique. An identical retry reuses the
existing checkpoint. Different evidence at the same identity raises source
drift and never overwrites the record. Missing candle intervals, broken
checkpoint counts and report-hash mismatches fail closed.

## Drift evidence

After the first complete post-freeze fold, the monitor compares:

- forward-only market-state share against the frozen reference;
- per-state challenger-minus-baseline outcome per bar;
- the rolling actual/2x/3x execution-cost and 2x modeled-cost surface;
- latest fold return delta and cumulative post-freeze win rate.

Fixed alarms include state-mix drift, state-outcome deterioration, cost
sensitivity deterioration, material latest-fold loss and forward-fold reversal.
Every alarm states severity, trigger, impact, evidence, recommended response and
closure condition. Responses require data review or continued frozen
observation—never retuning.

At four complete post-freeze folds, the monitor automatically recomputes the
same MIL-3.29 checks. A passing result remains human-review evidence only; all
proposal, activation and live-execution authority stays false.

## Explicit local operation

Read status without creating evidence:

```bash
python run_frozen_evidence_monitor.py \
  --db mil3_market.sqlite \
  --action STATUS
```

Perform one idempotent collection wake:

```bash
python run_frozen_evidence_monitor.py \
  --db mil3_market.sqlite \
  --action WAKE
```

Run the bounded scheduler for a fixed number of hourly checks:

```bash
python run_frozen_evidence_monitor.py \
  --db mil3_market.sqlite \
  --action FOREGROUND \
  --poll-seconds 3600 \
  --max-cycles 24
```

`--max-cycles 0` runs until interrupted. No Mac LaunchAgent is installed by
this milestone; deployment remains a separate decision.

The console reads only:

```text
GET /api/v1/frozen-forward-evidence
GET /api/v1/frozen-forward-evidence?snapshot_id=<eligible_v2_snapshot_id>
```

The browser cannot trigger `WAKE` or `FOREGROUND`.

## First real checkpoint

- Source snapshot: `aaf51f130fdcf43d0bd65ec5`
- Frozen specification: `a5d1c335f68be93cee8df770a77363e14d15ab1b321a4d45adefb92d9c3ba450`
- Checkpoint zero: `94e86430a12e442bd1a126a1`
- Validation boundary: `2026-08-30T03:00:00Z`
- Complete post-freeze folds: `0 / 4`
- Drift: `INSUFFICIENT_FORWARD_EVIDENCE`, severity `NONE`
- Next fold eligible after: `2026-09-08T08:00:00Z` (`16:00` Asia/Shanghai)

An immediate repeated wake returned `WAITING`, archived zero rows and preserved
SQLite integrity. This is the expected state until actual time and complete
market data reach the next canonical boundary.
