# MIL-3.28 Low-Turnover Deadband Challenger

MIL-3.28 tests one isolated AARS challenger on the exact fully closed v2 evidence used by MIL-3.27. It is research-only and has no configuration-registry, runtime or order path.

## Challenger policy

The baseline remains unchanged as `AARS_DYNAMIC`. The challenger is `AARS_DEADBAND_CHALLENGER` with:

- 12-bar minimum between ordinary same-direction changes;
- 0.95 exposure scale;
- state deadbands: 0.12 Accumulation, 0.10 Recovery, 0.20 Range, 0.08 Breakout, 0.08 Trend Expansion, 0.05 Distribution and 0.05 Breakdown;
- immediate action for direction changes;
- immediate entry into Distribution or Breakdown handling.

The strategy returns no action while a proposed exposure remains inside the relevant deadband or before the ordinary interval expires. This prevents price/equity-relative quantity recalculation from generating a small fill every hour.

## Four-way replay

Baseline and challenger each run twice:

| Replay | Fee | Slippage | Funding |
|---|---:|---:|---:|
| Actual modeled cost | 0.05% | 0.02% | archived Binance public history |
| True zero cost | 0 | 0 | 0 |

The zero-cost result is a separate engine replay over the same candles, not the MIL-3.27 accounting add-back. Therefore:

- actual return delta measures the full modeled challenger difference;
- zero-cost policy delta compares strategy paths with costs disabled;
- true cost-effect reduction compares each strategy's zero-cost and actual-cost reruns;
- none of these establishes causal performance outside the archived window.

## Real v2 result

Source snapshot: `aaf51f130fdcf43d0bd65ec5`, fully closed at `2026-08-30T03:00:00Z`.

| Metric | Baseline | Challenger | Delta |
|---|---:|---:|---:|
| Actual-cost return | -2.4357% | +8.8356% | +11.2714 points |
| Zero-cost return | +12.5234% | +15.5234% | +3.0000 points |
| Portfolio max drawdown | 14.9551% | 6.0597% | -8.8954 points |
| Turnover multiple | 187.17x | 80.31x | -57.09% |
| Simulated fills | 6,126 | 705 | -88.49% |
| Modeled cost return | 13.3745% | 5.8899% | -7.4846 points |
| Max liquidation-risk approximation | 0.3947% | 0.3899% | lower |
| Liquidation events | 0 | 0 | unchanged |

The internal research gate is `PROMISING_CHALLENGER`. This means only that turnover, actual return, drawdown and liquidation-risk checks pass on this one archived experiment. Independent walk-forward and multi-window validation remain mandatory. Proposal creation and all activation paths remain disabled.

## Read-only interfaces

```bash
python run_low_turnover_challenger.py \
  --db mil3_market.sqlite \
  --output-json reports/mil328-challenger.json
```

```text
GET /api/v1/low-turnover-challenger
GET /api/v1/low-turnover-challenger?snapshot_id=<eligible_v2_snapshot_id>
```

The browser uses GET only. It shows the identical evidence boundary, four-way cost matrix, turnover/risk checks and per-asset deltas. It cannot create a proposal, activate a challenger or execute a trade.

## Next evidence gate

MIL-3.29 should validate the fixed challenger without retuning across rolling train/test folds, several replay windows and adverse/sideways regimes. The MIL-3.28 real result must remain the frozen first experiment to avoid retrospective parameter selection.
