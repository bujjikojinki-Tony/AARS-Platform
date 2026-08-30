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

MIL-3.26 tightens that boundary to fully closed candles only. At evaluation time
`observed_at`, a candle is eligible only when `open_time + timeframe <=
observed_at`. Validation and portfolio replay share the same synchronized closed
boundary, and v2 snapshots record the per-asset boundary, timeframe duration,
observation date and `fully_closed=true` evidence explicitly.

Only one canonical snapshot per target strategy and UTC observation date may be
archived. An identical rerun is idempotent; changed same-day evidence fails
closed instead of increasing the governance history count. Run the archive once
per UTC day after ingestion and after the intended candle has fully closed.

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
snapshot ID, synchronized closed evidence time, UTC observation date, finality
state and review disposition. Rerunning the
same market evidence with only different generation timestamps returns the
same ID and does not add a row. Changed evidence creates a new immutable row
only on a later UTC observation date.

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

## MIL-3.27 diagnostic view

`GET /api/v1/strategy-diagnostics` selects the latest eligible fully closed v2
snapshot and replays its exact boundary through the common PAPER_ONLY ledger.
The report is trusted only when every reconstructed AARS asset return matches
the immutable archive. It then exposes asset, direction, regime, turnover and
modeled-cost attribution plus the AARS-versus-Buy-and-Hold gap. Optimization
ideas remain explicitly gated challenger hypotheses; reading diagnostics never
creates evidence or changes a configuration. See `STRATEGY_DIAGNOSTICS.md`.

## MIL-3.13 local console

The localhost console now includes a task-centered Continuous Shadow Evidence
workspace. It shows the Latest Stable Snapshot, Review Gate, history trust,
safe next step, return/liquidation-risk drift, recurring warning memory, daily
parameter changes and human-readable per-asset snapshot evidence.

The UI performs only GET requests. Changing the validation-strategy filter,
refreshing the evidence or selecting a snapshot never creates an archive. If
the API is unavailable, the workspace displays a degraded recovery state and
does not fabricate sample daily history.

## MIL-3.14 promotion governance

The local console also evaluates a conservative advisory promotion policy over
immutable daily evidence. It distinguishes insufficient or unstable evidence
(`CONTINUE_OBSERVATION`) from material adverse evidence (`REJECT_PROMOTION`) and
fully passing evidence (`PROMOTION_CANDIDATE`). A candidate remains subject to
separate human PAPER_ONLY review; automatic strategy change and live execution
are always disabled. See `PROMOTION_GOVERNANCE.md` for thresholds and rejection
bands.

## MIL-3.15 governed paper proposal

After and only after a `PROMOTION_CANDIDATE`, an explicit local command can
archive an immutable proposal packet. The console shows the baseline/proposed
parameter difference, observed risk boundary, source evidence, stop condition
and human review state. Review outcomes are terminal and immutable, but
acknowledgement does not apply any setting. The API remains read-only. See
`PAPER_CONFIGURATION_PROPOSALS.md` for the commands and schema contract.

## MIL-3.16 governed paper trial

An acknowledged proposal can be replayed once against its fixed baseline on the
same source-window evidence. The result archives exact input hashes, per-asset
common-ledger summaries, proposed-minus-baseline deltas and hard stop outcomes.
The console keeps stop status and authority locks visible. No result applies a
configuration. See `PAPER_TRIALS.md`.

## Review interpretation

The combined daily review is `DEFER` when either validation is deferred or the
portfolio risk surface is degraded. Otherwise it is
`READY_FOR_SHADOW_REVIEW`. Every payload explicitly sets
`live_execution_allowed` to `false`.

A few daily snapshots are observation, not evidence of durability. Treat the
first seven as insufficient history, then review parameter churn, recurring
funding gaps, drawdown/risk drift, and consecutive ready snapshots together.
Archived v1 snapshots remain visible for audit but do not count toward promotion
after MIL-3.26 because they do not contain explicit closed-candle proof. The
30-day promotion evidence window therefore restarts with eligible v2 snapshots.

## Deferred Mac mini activation

No LaunchAgent or always-on service is installed by MIL-3.12. When the Mac mini
is ready, the operational schedule should run incremental ingestion first,
then this daily archive command, then the existing health check and backup.
Activation remains a separate, explicit deployment step using
`MAC_MINI_OPERATIONS.md`.
