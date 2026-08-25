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

Status: **implemented in PR #2**.

`aars_market.paper.PaperPortfolio` is the sole execution ledger. It supports signed long/flat/short inventory and exposes realized P&L, inventory unrealized P&L, fees, modeled slippage cost, funding, net exposure, effective leverage, margin buffer and maintenance-margin-based liquidation risk. It has no exchange client or order-submission interface.

### MIL-3.5 — Replay + Comparative Validation
Acceptance:
- Same historical period can replay all baseline strategies.
- Report includes return and risk metrics.
- AARS is not accepted as alpha-producing unless it improves risk-adjusted results out-of-sample.

Status: **implemented in PR #2**.

All four shadow strategies now run through `aars_market.simulation.ReplayEngine`:

1. `BUY_HOLD` — one-time 1x spot entry.
2. `SPOT_GRID` — long-only symmetric grid bounded to 0–1x.
3. `FUTURES_LONG_GRID_10X` — parameterized leveraged long grid (10x default) with funding, maintenance margin and an optional state-aware tactical hedge.
4. `AARS_DYNAMIC` — evidence-driven Long / Flat / Tactical Short exposure.

Every strategy uses the same fill, fee, slippage, funding, equity and risk calculations. The comparison reports Total Return, Max Drawdown, Sharpe, Sortino, Profit Factor, Turnover, Fees, Slippage, Funding, realized grid P&L, inventory unrealized P&L, Net Exposure, Effective Leverage, Margin Buffer and Liquidation Risk.

### Deterministic replay conventions

- The replay starts at `warmup_bars - 1`; all feature/state inputs are limited to candles at or before the current bar.
- Grid levels are anchored to the first replay close and remain fixed for that run.
- Because OHLC candles do not contain tick order, intrabar crossings use one documented deterministic path: green/doji candle `previous close -> open -> low -> high -> close`; red candle `previous close -> open -> high -> low -> close`.
- A crossed grid level maps to a bounded target exposure. Reductions realize grid P&L; surviving inventory remains marked as unrealized P&L.
- Positive funding means longs pay and shorts receive. `--funding-rate-per-bar` is explicit and defaults to zero when no historical funding series is supplied.
- Liquidation Risk is an approximation, not an exchange liquidation engine. For an open position, margin buffer is `equity / absolute notional`; the risk score is `min(1, maintenance margin rate / margin buffer)`. A breach is recorded when margin buffer is at or below maintenance margin.
- Profit Factor uses gross positive equity changes divided by the absolute gross negative equity changes, so the definition is identical for inventory and state-driven strategies.
- Slippage is already embedded in execution price and therefore in P&L. The separate Slippage field is attribution only and is not deducted a second time.
- 10x is a stress-test parameter, not a recommendation. Fees and slippage can push effective leverage slightly above the requested target after a fill, which is intentionally visible in the report.

### Tactical hedge rule

The futures long grid remains long-only during normal grid operation. When enabled, its transparent state overlay:

- moves to flat in `DISTRIBUTION`;
- moves to a bounded paper short hedge in `BREAKDOWN` (20% of the configured leverage cap by default);
- returns to the last grid target after the bearish state clears.

`AARS_DYNAMIC` independently supports tactical short exposure through its existing state/probability policy. Neither path can submit a live order.

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

Status: **baseline implemented in PR #2**.

`mil3/ui/index.html` is a dependency-light, read-only research console consuming the versioned `mil3.dashboard.v1` payload. `run_compare.py --output-json ui/dashboard_payload.json` exports the payload from the same replay results printed by the CLI, including downsampled equity, drawdown, exposure, leverage, margin-buffer and liquidation-risk traces.

The main view continuously exposes PAPER_ONLY authority, data trust, highest liquidation risk, degraded conditions and Latest Stable View. It supports strategy selection and Equity/Risk trace inspection only; there are no order, credential or live-mode controls. Missing or invalid payloads fall back to an explicitly degraded deterministic demonstration dataset.

The HMI design and local run instructions are recorded in `mil3/ui/README.md`.

### MIL-3.7 — Funding History, Replay Views and Read-Only API

Status: **implemented in PR #2**.

- `run_funding_ingest.py` ingests real Binance USD-M public funding history without credentials. Funding events retain exchange timestamps, rate, mark price and rate type in SQLite.
- `ReplayEngine` applies funding only when the event timestamp has been reached. The legacy per-bar rate remains an explicit fallback and is ignored when timestamped history is present.
- `DashboardService` selects BTCUSDT, ETHUSDT or SOLUSDT and a 30d/90d/180d/365d/all replay window from persisted data.
- Explicitly archived dashboards are stored as immutable, content-addressed Latest Stable Views. Duplicate content resolves to the same archive identity.
- `run_archive.py` is the explicit archive write path; dashboard GET requests do not mutate SQLite.
- `run_api.py` serves the console and JSON endpoints on localhost. Only GET, HEAD and OPTIONS are allowed; POST, PUT, PATCH and DELETE return 405.
- The console can switch market/window, inspect archive history, and preserves the last displayed stable view if a requested refresh fails.

Read-only endpoints:

- `/api/v1/health`
- `/api/v1/markets`
- `/api/v1/dashboard?symbol=SOLUSDT&interval=1h&window=90d`
- `/api/v1/stable-views`
- `/api/v1/stable-views/{view_id}`

### MIL-3.8 — Incremental Operations, Coverage and Portfolio Risk

Status: **implemented on `mil-3-live-market-paper-trading`**.

- `IncrementalIngestor` starts from the latest persisted candle/funding timestamp with a configurable overlap. Existing idempotent upserts repair late revisions without duplicate history.
- `run_scheduler.py` provides a local, interruptible polling loop. `--max-cycles` bounds acceptance runs; the default `0` runs until the user stops it. It does not install a daemon or background service.
- Every cycle persists a PAPER_ONLY audit summary with per-symbol candle/funding success, cursor window, fetched/upserted count and sanitized error text.
- Funding coverage evaluates the replay interval against the expected 8-hour cadence and reports observed events, estimated gaps, coverage ratio, largest gap and leading/internal/trailing gap evidence. Missing or gapped history adds `FUNDING_COVERAGE_GAP` and defers the review gate.
- Cross-asset portfolio aggregation aligns full-resolution BTC/ETH/SOL replay traces for a selected shadow strategy. It reports portfolio equity, drawdown, net/gross exposure, effective leverage, minimum margin buffer, maximum liquidation risk and degraded assets.
- Portfolio capital uses independent equal-weight asset buckets. It deliberately makes no claim of exchange-level cross-margin or collateral netting.
- Stable View diff compares immutable archive evidence semantically. Generation timestamps and chart traces are excluded; state, probability, exposure, funding coverage, risk, strategy metrics and review disposition remain auditable changes.

Additional read-only endpoints:

- `/api/v1/ingestion-cycles`
- `/api/v1/portfolio?symbols=BTCUSDT,ETHUSDT,SOLUSDT&interval=1h&window=90d&strategy=AARS_DYNAMIC`
- `/api/v1/stable-view-diff?before={view_id}&after={view_id}`

### MIL-3.9 — Dynamic Binance Funding Cadence

Status: **implemented on `mil-3-live-market-paper-trading`**.

- Scheduled and one-shot funding ingestion query Binance USD-M public `fundingInfo` once per snapshot. Adjusted symbols persist `fundingIntervalHours`, rate cap/floor and disclaimer; a successfully returned snapshot records omitted configured symbols as explicit `DEFAULT_ABSENT` 8-hour observations.
- A failed `fundingInfo` request never invents default observations. The audit cycle records the failure separately while candle and funding-history ingestion may continue.
- Cadence observations are timestamped locally because Binance exposes the current adjustment snapshot without an effective-from timestamp or historical cadence series. Replay coverage applies a piecewise schedule only from the first locally observed timestamp; earlier periods disclose `DEFAULT_8H_FALLBACK` provenance.
- Funding-gap detection uses cadence-equivalent units. For example, an 8-hour separation under an observed 4-hour schedule is two expected intervals and identifies one missing event.
- Dashboard, portfolio evidence and the console distinguish replay-window cadence from the current effective snapshot so a temporary adjustment is visible without rewriting older replay assumptions.

Additional read-only endpoint:

- `/api/v1/funding-cadence?symbol=SOLUSDT`

### MIL-3.10 — Mac mini Long-Running Operations

Status: **implemented on `mil-3-live-market-paper-trading`**.

- `run_macos_service.py` renders, installs, inspects and uninstalls four narrowly scoped user LaunchAgents for scheduler, localhost API, health and daily maintenance.
- The scheduler remains the only market-data writer. The operational health command opens SQLite read-only, verifies database integrity, checks the latest ingestion-cycle status/age and evaluates BTC/ETH/SOL candle freshness.
- `run_backup.py` uses SQLite's online backup API, verifies the completed copy, reports SHA-256 evidence and prunes only scoped backups after the configured retention period.
- Daily maintenance bounds LaunchAgent text logs with copy-and-truncate rotation. Uninstall removes only AARS property lists and preserves the database, logs and backups.
- Generated service definitions use resolved absolute paths and force the API to `127.0.0.1`; no public bind or execution route is added.
- User LaunchAgents resume after the FileVault user logs in following a reboot. A privileged LaunchDaemon and automatic-login exception are intentionally out of scope.

The installation, health, backup, upgrade and restore procedures are documented in `mil3/MAC_MINI_OPERATIONS.md`.

### MIL-3.11 — Strategy Robustness Validation

Status: **implemented on `mil-3-live-market-paper-trading`**.

- `run_validate.py` provides deterministic chronological walk-forward validation for AARS Dynamic, Spot Grid and Futures Long Grid parameter grids.
- Every fold separates indicator warmup, scored training bars and the immediately following scored test bars. Parameter ranking and selection use training results only; test data never feeds back into selection.
- The selected candidate and Buy & Hold share the existing ReplayEngine/PaperPortfolio accounting on the same test interval, retaining fees, slippage, funding, drawdown, turnover, exposure, leverage, margin buffer and liquidation-risk evidence.
- Reports expose training rankings, parameter sensitivity, selection stability, train/test score decay, descriptive test regimes and explicit overfitting/risk warnings.
- Multi-asset mode runs the same experiment for BTCUSDT, ETHUSDT and SOLUSDT and preserves every per-asset report. Its aggregate is a comparison of evidence, not a cross-margin portfolio simulation.
- HIGH warnings—including insufficient folds, material score decay, baseline underperformance or liquidation approximation breaches—force `DEFER`. Every report keeps `live_execution_allowed=false`.

The fold contract, ranking score, warnings and commands are documented in `mil3/ROBUSTNESS_VALIDATION.md`.

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
python run_funding_ingest.py --db mil3_market.sqlite --days 365
python run_scheduler.py --db mil3_market.sqlite --poll-seconds 3600 --max-cycles 1
python run_archive.py --db mil3_market.sqlite --symbol SOLUSDT --window 90d
python run_replay.py --db mil3_market.sqlite --symbol SOLUSDT --interval 1h
python run_compare.py \
  --db mil3_market.sqlite \
  --symbol SOLUSDT \
  --interval 1h \
  --futures-leverage 10 \
  --grid-spacing 0.01 \
  --grid-levels 5 \
  --output-json ui/dashboard_payload.json
python run_api.py --db mil3_market.sqlite --port 8765
python run_healthcheck.py --db mil3_market.sqlite
python run_validate.py \
  --db mil3_market.sqlite \
  --symbols BTCUSDT ETHUSDT SOLUSDT \
  --strategy AARS_DYNAMIC \
  --output-json validation-multi-asset.json
python -m pytest -q
```

The ingestion and scheduler commands touch only public market-data endpoints. Replay, comparison, portfolio aggregation, archive diff and tests are local after ingestion. Every runner declares `execution_mode=PAPER_ONLY`; the local API adds no order route and GET requests do not mutate SQLite. Binance `fundingInfo` is a current adjustment snapshot, so preserving locally observed cadence history is required for auditable replay rather than retroactively applying today's interval.

## MIL-3.5 verification

- Deterministic tests cover ledger realization, long-to-short crossing, funding direction, explicit slippage, leverage/margin/liquidation approximation, four-strategy comparison, separated grid/inventory P&L, parameterized 10x futures simulation and Tactical Hedge activation.
- Acceptance command: `python -m pytest -q` from `03_Projects/Polymarket/mil3`.
- Live-order guard: MIL-3 contains only public market-data adapters and paper accounting. No authenticated trading adapter, credential field or order endpoint is introduced.
- MIL-3.9 deterministic tests cover 4-hour adjustment decoding, complete snapshot materialization, failed-snapshot behavior, idempotent cadence storage, piecewise coverage gaps, explicit fallback provenance and the read-only cadence API.
- MIL-3.10 deterministic tests cover read-only health behavior, missing/stale/partial failure modes, consistent online backup, scoped retention, bounded log rotation, absolute launchd definitions, localhost-only API binding and data-preserving uninstall.
- MIL-3.11 deterministic tests cover parameter-grid caps, chronological fold boundaries, training-only selection, strict finite JSON, common-ledger evidence, multi-asset aggregation and CLI report generation.

## Definition of Done

MIL-3 is complete when AARS can ingest current BTC/ETH/SOL data, classify state with evidence, produce calibrated probability outputs, execute only in a paper ledger, replay historical periods, compare strategies and expose the result through an auditable API/UI without any live-order capability.
