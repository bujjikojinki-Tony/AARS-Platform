# MIL-3.29 Frozen Challenger Robustness Validation

MIL-3.29 freezes the complete MIL-3.28 challenger before evaluating other time
windows, chronological weekly folds, market states and modeled-cost stresses.
It performs no candidate selection or parameter search and grants no proposal,
configuration, runtime or live-execution authority.

## Immutable experiment contract

The content-addressed specification includes the source v2 snapshot, freeze
time, 12-bar ordinary interval, 0.95 exposure scale, all seven state deadbands
and both immediate-transition rules. Every window, fold and stress row carries
the same SHA-256. Changing any field creates a different experiment; it cannot
be included in the frozen report.

Validation uses the existing PAPER_ONLY replay ledger. Baseline and challenger
receive identical candles, funding history, warmup and portfolio weights. Test
folds are chronological, contain 168 scored hourly bars and advance 168 bars.
Warmup may precede a fold, but no fold selects or changes the strategy.

Time lineage is explicit:

- `PRE_DISCOVERY_HOLDOUT`: predates the original 90-day discovery window;
- `DISCOVERY_WINDOW_REUSE`: retrospective reuse, never independent evidence;
- `POST_FREEZE_FORWARD`: fully closed evidence after the fixed freeze time;
- `BOUNDARY_CROSSING`: mixed lineage, excluded from independent claims.

The discovery boundary is permanently anchored to the freeze time. It does not
move when new candles arrive.

## Stress scenarios

The fixed 90-day comparison runs under actual modeled cost, 2x and 3x execution
cost, and 2x fees/slippage/funding history. Funding scaling preserves the sign
of each archived event, so it is a signed-history sensitivity test rather than
a claim that every scaled funding event is adverse.

## Real evidence result

Source snapshot `aaf51f130fdcf43d0bd65ec5`; validation boundary
`2026-08-30T04:00:00Z`; frozen specification SHA-256
`a5d1c335f68be93cee8df770a77363e14d15ab1b321a4d45adefb92d9c3ba450`.

| Window | Return delta | Drawdown delta | Turnover reduction |
|---|---:|---:|---:|
| 30d | +3.5616 points | -1.2454 points | 63.42% |
| 60d | +8.3803 points | -7.0434 points | 58.22% |
| 90d | +11.2367 points | -8.8953 points | 57.13% |
| 120d | +14.2246 points | -11.3763 points | 50.83% |

The frozen strategy wins 3/3 pre-discovery weekly folds and 11/12 reused
discovery folds. Seven market states are observed. ACCUMULATION, BREAKDOWN and
BREAKOUT have adverse state-attributed deltas, so the aggregate improvement is
not uniform across regimes. All four cost scenarios satisfy the fixed survival
gate and mean rolling turnover reduction is 53.11%.

The final disposition is nevertheless `WAIT_FOR_POST_FREEZE_EVIDENCE` and the
overfit assessment is `HIGH`: zero complete weekly post-freeze folds exist.
Retrospective breadth cannot replace elapsed forward time. Parameters must stay
unchanged until at least four complete post-freeze weekly folds exist, with the
remaining gates re-evaluated unchanged.

## Read-only use

```bash
python run_frozen_challenger_robustness.py \
  --db mil3_market.sqlite \
  --snapshot-id aaf51f130fdcf43d0bd65ec5 \
  --output-json reports/mil329-robustness.json
```

```text
GET /api/v1/frozen-challenger-robustness
GET /api/v1/frozen-challenger-robustness?snapshot_id=<eligible_v2_snapshot_id>
```

The endpoint and console are GET-only. Missing or mismatched source evidence
fails closed, withholds all evaluation rows and displays the exact recovery
condition. No MIL-3.29 result can tune parameters, create a proposal, activate
the challenger or submit an order.

MIL-3.30 now preserves checkpoint zero and automatically appends each new
complete post-freeze weekly fold under this same specification and gate. See
`FROZEN_FORWARD_EVIDENCE.md`.
