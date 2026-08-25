# MIL-3.17 Forward-Only Extended Paper Observation

MIL-3.17 observes an eligible MIL-3.16 proposed configuration only on market
data that arrived after the archived trial evidence boundary. It compares the
unchanged baseline and proposed candidates on the same synchronized assets,
cost model and paper ledger. It remains advisory and cannot apply either
configuration.

## Eligibility and boundary

An observation fails closed unless the archived trial disposition is
`ELIGIBLE_FOR_EXTENDED_PAPER_OBSERVATION`, its stop condition is clear and all
PAPER_ONLY authority locks are intact.

For every asset:

- the anchor is the trial asset's immutable `evidence_end`;
- performance begins on the first candle whose open time is strictly greater
  than that anchor;
- exactly `warmup_bars - 1` candles ending at the anchor provide feature
  context only;
- warmup candles do not contribute returns, fees, slippage, funding, turnover
  or risk;
- the checkpoint end is the minimum latest candle time across all assets, so
  no faster feed receives extra evidence.

The archive records the boundary per asset and labels historical replay as
excluded.

## Funding completeness

Funding-dependent candidates require `COMPLETE` history from the first forward
bar through the synchronized checkpoint end. Coverage uses locally archived
Binance cadence observations and supports temporary schedules such as 4h.
Missing or gapped coverage prevents the checkpoint from being created.

## Checkpoints and lineage

Each checkpoint hashes every consumed warmup and forward candle plus the
forward funding rows and cadence evidence for every asset, then records a
combined input hash. Warmup is hashed for reproducibility even though it is
excluded from performance. Checkpoints are append-only:

- rerunning the same endpoint and evidence is idempotent;
- different evidence at an existing endpoint is rejected;
- a new endpoint links to the previous observation ID and input hash;
- an endpoint older than the latest archived checkpoint is rejected.

This is evidence continuity, not an exchange execution log.

## Advisory outcomes

The default minimum checkpoint is 24 forward bars. Confirmation requires 168
forward bars unless explicitly changed for a controlled paper experiment.

- `CONTINUE_FORWARD_OBSERVATION`: enough data for a checkpoint, but not yet the
  confirmation horizon;
- `PROPOSED_EDGE_CONFIRMED`: confirmation horizon reached and the proposed
  aggregate risk-adjusted score is at least the baseline score;
- `PROPOSED_EDGE_NOT_CONFIRMED`: confirmation horizon reached without that
  improvement;
- `STOP_FORWARD_OBSERVATION`: drawdown, liquidation-risk or liquidation-event
  stop triggered.

No disposition applies parameters or permits live execution.

## Explicit local write path

```bash
python run_forward_observation.py \
  --db mil3_market.sqlite \
  --trial-id <eligible_trial_id> \
  --minimum-forward-bars 24 \
  --confirmation-bars 168
```

`--as-of <ISO-8601>` may create a deterministic checkpoint at an earlier common
market boundary, provided it is newer than the latest archived checkpoint.

## Read-only API

```text
GET /api/v1/forward-observations?strategy=AARS_DYNAMIC&limit=30
GET /api/v1/forward-observations?trial_id={trial_id}&limit=30
GET /api/v1/forward-observations/{observation_id}
```

Every index and detail envelope explicitly sets:

```text
observation_application_allowed=false
automatic_strategy_change_allowed=false
live_execution_allowed=false
```
