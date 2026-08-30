# MIL-3.27 Strategy Diagnostic and Cost Attribution

MIL-3.27 explains an archived AARS Dynamic PAPER_ONLY result. It does not select, apply or activate parameters and it adds no order path.

## Evidence contract

The diagnostic selects the latest promotion-eligible `mil3.shadow-daily.v2` snapshot unless an explicit snapshot ID is requested. It replays the exact archived symbols, timeframe, window, warmup and fully closed `as_of` boundary through the existing common ledger. Every AARS asset return must match the immutable archived asset return within `1e-10`; otherwise the report is `DEGRADED`, attribution is withheld and no hypothesis is issued.

The output separates:

- AARS versus equal-weight Buy & Hold return gap;
- weighted asset contribution to that gap;
- Long, Flat and Tactical Short accounting changes;
- market-state accounting changes;
- fills, direction reversals, turnover and turnover multiple;
- fees, slippage and funding;
- drawdown, exposure, leverage, margin buffer and liquidation-risk approximation.

`accounting_cost_reversal_return` adds modeled fees, slippage and funding back to observed equity. It is an accounting sensitivity, not an execution forecast or causal estimate. Regime/direction groups are descriptive ledger attribution, not proof of strategy alpha.

## Read-only usage

```bash
python run_strategy_diagnostics.py \
  --db mil3_market.sqlite \
  --output-json reports/mil327-diagnostic.json
```

The localhost API exposes:

```text
GET /api/v1/strategy-diagnostics
GET /api/v1/strategy-diagnostics?snapshot_id=<immutable_v2_snapshot_id>
```

The console shows stable-versus-latest-raw boundaries, data trust, the highest asset drag, baseline gap, modeled cost drag, per-asset evidence and a findings queue. Evidence rows describe observed accounting. Hypothesis rows always require a separate deterministic challenger replay. There are no browser controls for strategy changes, activation or execution.

## Current real v2 diagnostic

For snapshot `aaf51f130fdcf43d0bd65ec5` at the fully closed `2026-08-30T03:00:00Z` boundary, reconstruction passes for BTC, ETH and SOL:

- AARS equal-weight return: `-2.4357%`;
- Buy & Hold equal-weight return: `+49.7583%`;
- AARS gap: `-52.1940%`;
- weighted modeled cost drag: `13.3745%`;
- largest modeled cost: fees;
- largest asset gap contributor: ETH;
- asset turnover: approximately `181.9x` to `193.8x` initial capital over the 90-day replay.

This supports a lower-turnover challenger as the first optimization experiment. It does not authorize changing the fixed PAPER_ONLY configuration.

MIL-3.28 implements that isolated experiment with a true zero-cost engine comparison. See `LOW_TURNOVER_CHALLENGER.md`; the MIL-3.27 diagnostic and accounting-add-back contract remains unchanged.

## Recovery

- `NO_ELIGIBLE_V2_STABLE_SNAPSHOT`: archive one fully closed canonical daily v2 snapshot.
- `EVIDENCE_BOUNDARY_UNAVAILABLE`: restore the source candles through the archived boundary.
- `ARCHIVED_RETURN_MISMATCH`: preserve the database, inspect source drift/tampering and do not use the attribution.
- `SNAPSHOT_NOT_ELIGIBLE_V2_EVIDENCE`: retain it for audit but select an eligible v2 snapshot.

All responses explicitly keep automatic strategy change, configuration activation and live execution disabled.
