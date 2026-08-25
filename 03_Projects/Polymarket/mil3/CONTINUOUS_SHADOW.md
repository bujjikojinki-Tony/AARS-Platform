# MIL-3.12 Continuous Shadow Evidence

MIL-3.12 turns one-off robustness reports into an auditable daily PAPER_ONLY
evidence history. It does not schedule itself, submit orders, manage exchange
credentials, or authorize live execution.

## Daily evidence contract

One explicit daily run performs this local sequence:

```text
stored BTC/ETH/SOL candles + funding
  -> MIL-3.11 train-only walk-forward validation
  -> existing equal-weight shadow portfolio replay
  -> combined review gate
  -> immutable SQLite snapshot
  -> read-only stability timeline
```

The validation target and portfolio strategy are separate configuration fields.
Validation-selected parameters are research evidence only. The portfolio uses
the existing fixed strategy defaults; MIL-3.12 does not silently promote a
candidate into the monitored portfolio.

`as_of` is the oldest of the latest candles across the selected assets. This is
the last synchronized evidence boundary. Per-asset evidence times remain in
`evidence_as_of`.

## Archive one daily snapshot

From `03_Projects/Polymarket/mil3`, after an incremental ingestion cycle:

```bash
python run_shadow_daily.py \
  --db mil3_market.sqlite \
  --symbols BTCUSDT ETHUSDT SOLUSDT \
  --interval 1h \
  --window 90d \
  --validation-strategy AARS_DYNAMIC \
  --portfolio-strategy AARS_DYNAMIC \
  --warmup 120 \
  --train-bars 2160 \
  --test-bars 720 \
  --step-bars 720 \
  --aars-exposures 0.25,0.5,0.75,1
```

The command is the only MIL-3.12 write path. It prints the content-addressed
snapshot ID, synchronized evidence time, and review disposition. Rerunning the
same market evidence with only different generation timestamps returns the
same ID and does not add a row. Changed evidence creates a new immutable row.

For 10x futures-grid stress validation:

```bash
python run_shadow_daily.py \
  --db mil3_market.sqlite \
  --validation-strategy FUTURES_LONG_GRID \
  --futures-leverages 2,5,10 \
  --grid-spacings 0.005,0.01,0.02 \
  --grid-levels 3,5 \
  --hedge-modes both
```

This remains an approximation-only stress test. A 10x candidate is not a
deployment recommendation.

## Read-only local API

With `run_api.py` bound to localhost, these GET endpoints are available:

```text
/api/v1/shadow-snapshots?limit=30&strategy=AARS_DYNAMIC
/api/v1/shadow-snapshots/{snapshot_id}
/api/v1/shadow-stability?limit=90&strategy=AARS_DYNAMIC
```

The stability response shows, in chronological order:

- latest selected candidate per asset;
- validation return and parameter-selection stability;
- recurring, added, and resolved warning codes;
- portfolio return, drawdown, exposure, leverage, margin buffer, and
  liquidation-risk approximation;
- candidate changes and review-gate transitions;
- insufficient-history and parameter-churn warnings.

All API methods other than GET, HEAD, and OPTIONS remain rejected. Reading the
history or stability view never archives or modifies a snapshot.

## Review interpretation

The combined daily review is `DEFER` when either validation is deferred or the
portfolio risk surface is degraded. Otherwise it is
`READY_FOR_SHADOW_REVIEW`. Every payload explicitly sets
`live_execution_allowed` to `false`.

A few daily snapshots are observation, not evidence of durability. Treat the
first seven as insufficient history, then review parameter churn, recurring
funding gaps, drawdown/risk drift, and consecutive ready snapshots together.

## Deferred Mac mini activation

No LaunchAgent or always-on service is installed by MIL-3.12. When the Mac mini
is ready, the operational schedule should run incremental ingestion first,
then this daily archive command, then the existing health check and backup.
Activation remains a separate, explicit deployment step using
`MAC_MINI_OPERATIONS.md`.
