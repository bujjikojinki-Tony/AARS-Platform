# MIL-3.16 Governed Paper Trial Results

MIL-3.16 runs one isolated, synchronous PAPER_ONLY comparison for an
acknowledged MIL-3.15 proposal. The recorded baseline and proposed candidate use
the same stored candles, funding history, evidence boundary, replay window,
warmup, capital, fees, slippage and maintenance-margin approximation.

The trial never changes a portfolio default, proposal, scheduler, exchange
account or live strategy.

## Eligibility

A trial fails closed unless:

- the proposal is archived and has one terminal
  `ACKNOWLEDGED_FOR_PAPER_TRIAL` review;
- proposal, review and source snapshot are all `PAPER_ONLY` and explicitly deny
  application, automatic strategy change and live execution;
- source strategy, symbols, timeframe, replay window, warmup and per-asset
  evidence boundaries are valid;
- each asset has enough candles at the archived boundary;
- cadence-aware funding coverage is `COMPLETE` when either candidate uses
  funding. Coverage honors archived Binance cadence observations, including
  temporary 4h schedules, and records fallback provenance.

## Common comparison

Both configurations run through the existing `ReplayEngine` and common paper
ledger. The result retains per-asset summaries and reports:

- mean total return, Sharpe, Sortino and finite Profit Factor;
- worst-asset drawdown, leverage, margin buffer and liquidation risk;
- summed turnover, fees, slippage, funding, realized P&L, realized grid P&L and
  inventory unrealized P&L;
- proposed-minus-baseline deltas for every comparable metric.

The capital model is independent equal-capital asset buckets. It does not imply
exchange cross-margin netting.

## Input identity

Every asset receives a SHA-256 hash over the exact candles and funding rows
consumed, including the cadence observations used for completeness checks. A
combined hash covers the whole trial. The source shadow snapshot
records evidence boundaries but does not embed raw market rows, so the trial
states that reproducibility boundary explicitly.

## Stop conditions and advisory outcomes

Default stops are:

- proposed worst-asset drawdown greater than 20%;
- proposed maximum liquidation-risk approximation greater than 10%;
- any liquidation approximation breach.

The advisory disposition is one of:

- `STOP_TRIAL`: a hard stop was triggered;
- `CONTINUE_BASELINE`: no hard stop, but the proposed aggregate risk-adjusted
  score did not improve on the baseline;
- `ELIGIBLE_FOR_EXTENDED_PAPER_OBSERVATION`: no hard stop and the proposed
  aggregate risk-adjusted score was at least the baseline score.

None of these outcomes applies a configuration.

## Explicit local write path

```bash
python run_paper_trial.py \
  --db mil3_market.sqlite \
  --proposal-id <acknowledged_proposal_id> \
  --initial-equity-per-asset 1000 \
  --fee-rate 0.0005 \
  --slippage-rate 0.0002 \
  --maintenance-margin-rate 0.005 \
  --stop-max-drawdown 0.20 \
  --stop-max-liquidation-risk 0.10
```

One proposal may have one canonical immutable result. Rerunning identical inputs
and settings is idempotent. A conflicting result for the same proposal is
rejected to prevent result shopping.

## Read-only API

```text
GET /api/v1/paper-trials?strategy=AARS_DYNAMIC&limit=30
GET /api/v1/paper-trials/{trial_id}
```

The API remains GET/HEAD/OPTIONS only and every envelope explicitly sets:

```text
trial_application_allowed=false
automatic_strategy_change_allowed=false
live_execution_allowed=false
```
