# MIL-3.11 Robustness Validation

MIL-3.11 tests whether a PAPER_ONLY strategy configuration survives strict
chronological out-of-sample evaluation. It is a research gate, not evidence that
future returns are predictable and not authorization for live execution.

## Fold contract

Each fold has three ordered regions:

```text
indicator warmup -> scored training bars -> scored test bars
```

The test slice may reuse candles before its start only as indicator warmup. No
test candle is included in parameter scoring or selection. The candidate with
the highest training score is selected, then only that candidate and Buy & Hold
are evaluated on the following test period. Folds are never shuffled.

Required candles for the first fold are:

```text
warmup_bars - 1 + train_bars + test_bars
```

Subsequent folds advance by `step_bars`, which defaults to `test_bars`.

## Candidate grids

The target strategy determines which parameters are varied:

- `AARS_DYNAMIC`: maximum absolute exposure.
- `SPOT_GRID`: grid spacing and number of levels.
- `FUTURES_LONG_GRID`: leverage, grid spacing, levels and Tactical Hedge mode.

All candidates use the existing `ReplayEngine`, `PaperPortfolio`, funding
history, fee, slippage, maintenance-margin and liquidation-risk approximation.
The candidate cap prevents accidentally launching an unbounded combinatorial
experiment.

## Selection score

Training selection uses the declared bounded heuristic:

```text
clamped Sharpe
+ 0.5 * clamped Sortino
+ Total Return
- 2 * Max Drawdown
- 2 * Liquidation Risk
- 10 * Liquidation Events
```

Sharpe and Sortino are clamped to `[-5, 5]` before scoring. Exact score ties use
ascending candidate ID, making runs deterministic. This heuristic is for
ranking candidates inside a fold; it is not a statistical significance test.

## Evidence and warnings

The strict JSON report contains:

- complete chronological fold boundaries;
- every training candidate ranking;
- the training-selected candidate;
- selected-candidate and Buy & Hold test summaries;
- fees, slippage, funding, exposure, leverage, margin and liquidation evidence;
- training-score sensitivity and parameter-selection stability;
- test-period `UPTREND`, `DOWNTREND` or `RANGE` evidence;
- train/test score decay and Buy & Hold comparison;
- an explicit review disposition that never permits live execution.

Warnings include insufficient folds, a single-candidate grid, overlapping test
windows, unstable parameter selection, train/test score decay, Buy & Hold
underperformance, missing timestamped funding history and liquidation
approximation breaches. Any HIGH warning defers the review gate.

Test regimes are descriptive only. A test-period close change of at least +5%
is `UPTREND`, at most -5% is `DOWNTREND`, otherwise it is `RANGE`. Regime labels
never participate in training selection.

## Run one asset

From `03_Projects/Polymarket/mil3`:

```bash
python run_validate.py \
  --db mil3_market.sqlite \
  --symbol SOLUSDT \
  --interval 1h \
  --strategy AARS_DYNAMIC \
  --warmup 120 \
  --train-bars 2160 \
  --test-bars 720 \
  --step-bars 720 \
  --aars-exposures 0.25,0.5,0.75,1 \
  --output-json validation-sol.json
```

This example uses approximately 90 scored training days followed by 30 scored
test days for each 1H fold.

## Compare BTC, ETH and SOL

```bash
python run_validate.py \
  --db mil3_market.sqlite \
  --symbols BTCUSDT ETHUSDT SOLUSDT \
  --interval 1h \
  --strategy AARS_DYNAMIC \
  --train-bars 2160 \
  --test-bars 720 \
  --aars-exposures 0.25,0.5,0.75,1 \
  --output-json validation-multi-asset.json
```

The batch report preserves each asset's complete report and adds cross-asset
counts, mean asset returns, worst drawdown/liquidation risk and deferred assets.
It does not simulate portfolio capital allocation, cross-margin or collateral
netting.

## Grid examples

```bash
python run_validate.py \
  --db mil3_market.sqlite \
  --symbol SOLUSDT \
  --strategy SPOT_GRID \
  --grid-spacings 0.005,0.01,0.02 \
  --grid-levels 3,5 \
  --output-json validation-spot-grid.json

python run_validate.py \
  --db mil3_market.sqlite \
  --symbol SOLUSDT \
  --strategy FUTURES_LONG_GRID \
  --futures-leverages 2,5,10 \
  --grid-spacings 0.005,0.01,0.02 \
  --grid-levels 3,5 \
  --hedge-modes both \
  --output-json validation-futures-grid.json
```

The 10x candidate remains a stress-test configuration. It must not be treated as
a deployment recommendation, especially when liquidation or score-decay
warnings are present.
