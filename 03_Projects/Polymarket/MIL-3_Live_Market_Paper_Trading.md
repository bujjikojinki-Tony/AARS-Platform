# MIL-3 — Live Market Intelligence + Paper Trading

## Mission

Turn AARS crypto research from screenshot/manual analysis into a reproducible evidence pipeline driven by market data, while preserving the existing safety invariant: **no live-money execution**.

## Primary objective

For BTC/USDT, ETH/USDT and SOL/USDT, continuously transform market observations into:

`Observation -> Evidence -> MarketState -> Probability -> Decision -> PaperExecution -> Outcome -> Replay`

The system must answer three questions with auditable evidence:

1. What state is the market in now?
2. What is the probability distribution of relevant forward outcomes?
3. Does an AARS state-aware strategy outperform simple baselines after fees, funding and drawdown?

## Scope

### In scope
- Public REST market-data ingestion; no trading credentials required.
- BTCUSDT, ETHUSDT, SOLUSDT.
- 1h candles as the first canonical decision timeframe.
- OHLCV normalization and SQLite persistence.
- EMA 5/10/20/30/60, RSI14, ATR14 and Bollinger Bands.
- Deterministic market-state classifier.
- Bull/Base/Bear probability output with explicit evidence.
- Paper portfolio and replay/backtest interfaces.
- Baselines: Buy & Hold, Spot Grid, Futures Grid simulation, AARS Dynamic.
- Fees/funding/slippage fields in the accounting model.
- Risk metrics: total return, max drawdown, Sharpe, Sortino, win rate, profit factor, turnover, net exposure.
- UI/API-readable latest snapshot.

### Out of scope for MIL-3
- Real-money order submission.
- API keys with withdrawal/trading permission.
- Autonomous leverage escalation.
- LLM-only price prediction.
- Black-box neural forecasting before deterministic baselines are validated.

## Safety invariants

1. `execution_mode = PAPER_ONLY` by default and in acceptance tests.
2. No code path in MIL-3 may submit a live order.
3. Position sizing is capped by configured risk budget.
4. Forecasts are probability distributions, never guaranteed targets.
5. Every decision stores its input snapshot, evidence, model/version and outcome.
6. Backtests must include configurable fees and slippage; futures simulations must support funding cost.

## Market-state taxonomy

- ACCUMULATION
- RECOVERY
- RANGE
- BREAKOUT
- TREND_EXPANSION
- DISTRIBUTION
- BREAKDOWN

The first implementation is deterministic and explainable. ML may later learn residual probability calibration but must not replace the evidence record.

## Milestones

### MIL-3.1 — Market Data Gateway
Acceptance:
- Public market adapter returns normalized candles.
- SQLite upsert is idempotent.
- BTC/ETH/SOL can be updated without credentials.
- Adapter failure is explicit; stale data is never silently presented as live.

Implementation status: **implemented in PR #2**.

Current components:
- `aars_market.adapters.fetch_binance_spot_history()` paginates public Binance spot klines with an explicit page safety limit.
- `aars_market.storage.MarketStore` persists normalized candles in SQLite using `(symbol, timeframe, open_time)` as the idempotency key.
- `MarketStore.is_fresh()` provides an explicit freshness gate.
- `run_ingest.py` ingests BTCUSDT / ETHUSDT / SOLUSDT without credentials and always declares `PAPER_ONLY`.

### MIL-3.2 — Feature + State Engine
Acceptance:
- Features are reproducible from stored candles.
- No look-ahead in feature generation.
- Every state contains reason codes/evidence.

Implementation status: **baseline implemented**.

### MIL-3.3 — Probability Engine
Acceptance:
- Output probabilities sum to 1.
- Prior and evidence contributions are inspectable.
- Calibration can be evaluated on historical walk-forward windows.

Implementation status: **baseline priors implemented; walk-forward evaluation now available**.

The current Bull/Base/Bear probabilities are hypotheses, not trained forecasts. `aars_market.replay` evaluates them chronologically and reports Brier score so calibration can later replace hand-authored priors.

### MIL-3.4 — Paper Portfolio
Acceptance:
- Long/flat/short simulation supported.
- Net exposure, realized/unrealized P&L, fees, funding and slippage tracked separately.
- Liquidation-risk approximation supported for leveraged shadow strategies.

Status: **next implementation target**.

### MIL-3.5 — Replay + Comparative Validation
Acceptance:
- Same historical period can replay all baseline strategies.
- Report includes return and risk metrics.
- AARS is not accepted as alpha-producing unless it improves risk-adjusted results out-of-sample.

Status: **forecast replay foundation implemented; strategy replay pending MIL-3.4 ledger**.

### MIL-3.6 — UI
Minimum cards:
- Market State
- Evidence
- Bull/Base/Bear Probability
- Net Exposure
- Paper Portfolio P&L
- Max Drawdown
- Recommended Action
- Latest Stable View / data freshness

## Initial decision policy

The initial policy intentionally prefers risk control over activity:

- TREND_EXPANSION: allow controlled long exposure.
- RECOVERY: small/medium long only after confirmation.
- RANGE: favor low directional exposure; grid simulation may run.
- DISTRIBUTION: reduce long exposure.
- BREAKDOWN: disable new leveraged longs; tactical paper short may be evaluated.
- ACCUMULATION: staged spot accumulation simulation only.

## Validation horizon

- Historical replay: minimum 2 years where source data permits.
- Walk-forward evaluation: chronological split only.
- Shadow run: 30 days minimum before any discussion of live execution.

## Operational sequence

From `03_Projects/Polymarket/mil3`:

```bash
python run_ingest.py --db mil3_market.sqlite --days 120
python run_replay.py --db mil3_market.sqlite --symbol SOLUSDT --interval 1h
pytest -q
```

The first command touches only public market-data endpoints. The replay and tests are local/offline after data ingestion.

## Definition of Done

MIL-3 is complete when AARS can ingest current BTC/ETH/SOL data, classify state with evidence, produce calibrated probability outputs, execute only in a paper ledger, replay historical periods, compare strategies and expose the result through an auditable API/UI without any live-order capability.
