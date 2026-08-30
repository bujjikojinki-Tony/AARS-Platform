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

### MIL-3.17 — Forward-Only Extended Paper Observation

Status: **implemented on `mil-3-live-market-paper-trading`**.

- Only trials marked `ELIGIBLE_FOR_EXTENDED_PAPER_OBSERVATION` may start a checkpoint.
- Each asset begins measurement on the first candle strictly after its archived trial evidence boundary. Historical candles provide indicator warmup only and contribute no P&L, costs, funding or risk.
- Multi-asset checkpoints share the minimum latest candle time, preserving a common out-of-sample endpoint.
- Baseline and proposed candidates retain the exact trial parameters, capital, fees, slippage, maintenance margin and common `ReplayEngine` accounting.
- Funding-dependent candidates require cadence-aware `COMPLETE` funding coverage over the forward interval.
- Checkpoints are immutable, content-addressed and lineage-chained. Same-endpoint conflicting evidence, missing lineage and backward checkpoints are rejected.
- Outcomes remain advisory: continue observing, proposed edge confirmed/not confirmed, or stop forward observation. No outcome applies parameters or creates an execution route.
- The localhost API and console expose read-only index/detail evidence, leakage boundary, stop state, per-asset hashes and checkpoint lineage.

The contract and commands are documented in `mil3/FORWARD_OBSERVATION.md`.

### MIL-3.18 — Continuous Forward Observation Governance

Status: **implemented on `mil-3-live-market-paper-trading`**.

- `run_forward_monitor.py` provides a bounded or continuous local polling loop that advances every eligible trial by at most one immutable synchronized endpoint per cycle.
- The monitor is isolated from the ingestion scheduler, idempotently reuses unchanged endpoints, waits for insufficient history, degrades on evidence failures and skips trials after a hard stop.
- Read-only stability evaluates up to 30 checkpoints and requires at least 720 measured 1h bars plus three consecutive qualifying checkpoints before confirmation.
- Every checkpoint transition verifies predecessor observation ID and input hash; broken lineage or a gap above 48 hours defers review.
- Edge decay, edge reversal, rising liquidation risk and hard stops become structured alarms with trigger, impact, recommended response and closure condition.
- `EXTENDED_OBSERVATION_CONFIRMED` is evidence for human paper review only. Automatic strategy changes, parameter application and live execution remain prohibited.
- The console keeps horizon/streak progress, score/return deltas, risk, checkpoint trace and active alarms in the main forward-observation surface.

The scheduling and governance contract is documented in `mil3/CONTINUOUS_FORWARD_OBSERVATION.md`.

### MIL-3.19 — Human Forward Review and Evidence Export

Status: **implemented on `mil-3-live-market-paper-trading`**.

- Immutable local human-review events govern `OBSERVING`,
  `OBSERVING_ACKNOWLEDGED`, `PAUSED` and irreversible `TERMINATED` states.
- Acknowledgement requires confirmed extended-observation evidence; pause cannot
  conceal a hard stop; restart requires current non-stopped, non-deferred
  evidence.
- Each review is lineage-chained and bound to the latest checkpoint and derived
  stability hash. Storage independently rejects stale, changed or unauthorized
  evidence.
- The forward monitor does not generate checkpoints for paused or terminated
  candidates.
- Complete evidence exports contain the trial, every checkpoint, stability and
  human review with per-component and combined SHA-256 verification. Existing
  export files are never overwritten.
- The localhost API and console expose lifecycle, review history and manifest
  metadata read-only. Human writes remain explicit local CLI operations and no
  review applies parameters or authorizes live execution.

The lifecycle, commands and evidence contract are documented in
`mil3/HUMAN_FORWARD_REVIEW.md`.

### MIL-3.20 — Offline Evidence, Retention and Isolated Activation Approval

Status: **implemented on `mil-3-live-market-paper-trading`**.

- Exported bundles can be verified from JSON alone with strict duplicate-key
  rejection, complete hash reconstruction and PAPER_ONLY authority checks. No
  SQLite access is required.
- Verified bundles can be copied into a scoped archive with post-copy hash
  verification, immutable sidecars and inventory receipts, a 365-day default
  retention period and a minimum floor of two verified copies per trial.
- Pruning is fail-safe: only recognized artifacts whose content and filename
  identity both verify are eligible; unknown and lookalike files are preserved.
- Immutable isolated-activation decisions support approve, reject, bounded
  expiry and revoke. Approval requires confirmed/acknowledged warning-free
  evidence and storage independently rebuilds current hashes before insertion.
- Approval authorizes only a future named PAPER_ONLY sandbox. It does not apply
  a configuration, change shared defaults, start a strategy or permit live
  execution.
- Policy, lifecycle and review records are available through the GET-only local
  API and task-centered console. All decisions remain explicit local CLIs.

The offline and approval contract is documented in
`mil3/OFFLINE_EVIDENCE_AND_ACTIVATION_APPROVAL.md`.

### MIL-3.21 — Isolated PAPER_ONLY Configuration Registry

Status: **implemented on `mil-3-live-market-paper-trading`**.

- A current unexpired MIL-3.20 approval can be consumed exactly once into an
  immutable, inert configuration registry entry bound to its full payload and
  SHA-256.
- Each named sandbox has a versioned stored pointer plus append-only atomic
  events. Activation verifies state version, previous pointer/event, approval,
  expiry, sandbox ownership and authority under one SQLite transaction.
- Rollback consumes the latest unrolled activation once and revalidates its
  target. Unsafe rollback targets fail safe to the empty baseline.
- Read-only resolution separates stored pointer from effective configuration.
  Expired, revoked or mismatched approvals immediately return no effective
  configuration without mutating on GET.
- Explicit reconciliation can append the fail-safe invalidation event and clear
  the stored pointer. Effective invalidation does not depend on reconciliation.
- Registry selection starts no process, changes no shared configuration and has
  no connection to exchange credentials, orders or live execution.
- The GET-only API and console expose stored/effective state, configuration
  identity, rollback gates, blocking reason and the atomic event trail.

The registry and atomic lifecycle are documented in
`mil3/ISOLATED_PAPER_CONFIGURATION_REGISTRY.md`.

### MIL-3.22 — Governed Isolated PAPER_ONLY Runtime

Status: **implemented on `mil-3-live-market-paper-trading`**.

- Runtime acquisition consumes only the registry's current effective
  configuration and binds the session to its ID, SHA-256 and sandbox version.
- An opaque fencing token and a 5–300 second renewable lease prevent stale
  workers from retaining authority. Tokens are hashed in storage and omitted
  from every read-only API response.
- The sandbox kill switch fails safe to ARMED until explicitly cleared. ARM
  atomically stops every running session; CLEAR never restarts one.
- Heartbeats revalidate kill switch, lease, sandbox pointer/version, approval
  lineage/expiry and configuration hash before recording consumption.
- Read-only resolution immediately derives fail-safe states without GET writes;
  worker heartbeat or explicit reconciliation persists the stop event.
- The bounded worker records configuration-governance consumption only. It does
  not start replay, calculate paper orders, contact an exchange or expose live
  execution.
- The GET-only API and console expose stored/effective session state, heartbeat
  age, lease deadline, stop cause and immutable runtime/kill-switch events.

The runtime authority and recovery contract is documented in
`mil3/GOVERNED_ISOLATED_PAPER_RUNTIME.md`.

### MIL-3.23 — Deterministic Snapshot-to-Paper Ledger Runtime

Status: **implemented on `mil-3-live-market-paper-trading`**.

- Every valid runtime cycle selects the latest synchronized stored-candle
  boundary at or before cycle time and hashes candles, funding and cadence
  evidence per asset.
- Cycle identity is configuration/boundary based, so duplicate calls and crash
  recovery converge on one logical calculation across runtime sessions.
- `RESERVED` checkpoints, deterministic cumulative ReplayEngine results and
  append-only `RESERVE/RECOVER/COMMIT` events provide explicit recovery state.
- Commit rebuilds the reserved snapshot under a write lock. Source drift or
  changed lease/configuration authority blocks the result.
- Ledger result insertion and the `COMMITTED` checkpoint transition are atomic;
  a failure cannot leave an effective partial result.
- Committed cycles form a monotonic chain and repeated boundaries reuse the
  existing content-addressed result without double application.
- The GET-only API and console expose boundary/hash trust, checkpoint owner and
  attempts, ledger attribution, idempotency and recovery evidence.
- All calculations remain PAPER_ONLY using local public-market rows and the
  existing simulated accounting engine; no external order request exists.

The calculation, checkpoint and recovery contract is documented in
`mil3/DETERMINISTIC_RUNTIME_PAPER_LEDGER.md`.

### MIL-3.24 — PAPER_ONLY Shadow Strategy Bot Orchestrator

Status: **implemented on `mil-3-live-market-paper-trading`**.

- Each synchronized runtime snapshot now calculates Buy & Hold, Spot Grid,
  Futures Long Grid and AARS Dynamic as four isolated virtual accounts.
- Every bot uses the same content-addressed market inputs but keeps independent
  equity, position, costs, P&L, exposure, leverage, margin and risk evidence.
- Futures Long Grid retains the approved parameterized 10x setting and Tactical
  Hedge; AARS Dynamic retains Long / Flat / Tactical Short behavior.
- Deterministic simulated fills record price, quantity, notional, fees,
  slippage, realized contribution, category and reason without creating an
  external order request.
- Approved drawdown/liquidation thresholds flatten and freeze only the affected
  virtual account; they cannot change strategy, registry or execution authority.
- The four-bot fleet has its own content hash inside ledger v2 and commits under
  the existing atomic checkpoint. Legacy ledger v1 remains verifiable.
- The GET-only API and console expose each bot's account, unified metrics,
  simulated-fill count, current risk state and stop reason.

The fleet, accounting and risk-stop contract is documented in
`mil3/SHADOW_STRATEGY_BOTS.md`.

### MIL-3.25 — Forward Bot Operations

Status: **implemented on `mil-3-live-market-paper-trading`**.

- Runtime selection now rejects still-open candles and uses only the latest
  fully closed boundary synchronized across every configured asset.
- A one-shot forward wake starts a short fenced lease only when a new closed
  boundary is later than the latest commit; unchanged boundaries wait without
  creating sessions or cycles.
- Verified ledger v2 lineage produces per-bot and per-asset cycle deltas for
  equity, P&L, costs, positions, exposure, leverage, margin, risk and new fills.
- Content-addressed alerts expose configuration/kill blocks, stale or missing
  data, stale RESERVED work, result integrity, funding gaps and frozen bots.
- Burn-in evaluates the continuous closed-bar suffix at 7-day and 14-day gates;
  a gap over two intervals resets continuity.
- STATUS, WAKE and supervised FOREGROUND modes are explicit local commands. A
  separately rendered one-shot Mac LaunchAgent remains excluded from default
  install and is not loaded automatically.
- The GET-only API and console expose trigger, deltas, alerts and burn-in with
  no browser operation control.

The forward scheduling and burn-in contract is documented in
`mil3/FORWARD_BOT_OPERATIONS.md`.

### MIL-3.26 — Closed-Candle Daily Evidence Integrity

Status: **implemented on `mil-3-live-market-paper-trading`**.

- Daily validation and portfolio replay share one synchronized fully closed
  candle boundary.
- Immutable v2 snapshots record observation date, observed time, per-asset
  boundaries, timeframe duration and explicit finality proof.
- One target strategy can archive only one canonical snapshot per UTC
  observation date; identical reruns are idempotent and changed same-day reruns
  fail closed.
- Legacy v1 snapshots remain readable for audit and proposal lineage but are
  excluded from promotion-eligible history.
- Promotion governance reports archived versus eligible evidence and restarts
  its 30-day minimum from trustworthy v2 observations.

The daily evidence contract is documented in `mil3/CONTINUOUS_SHADOW.md`.

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
python run_forward_observation.py \
  --db mil3_market.sqlite \
  --trial-id <eligible_trial_id>
python run_forward_monitor.py \
  --db mil3_market.sqlite \
  --poll-seconds 3600 \
  --max-cycles 1
python run_forward_review.py \
  --db mil3_market.sqlite \
  --trial-id <trial_id> \
  --action PAUSE_PAPER_OBSERVATION \
  --reviewer local-owner \
  --note "Pause for human risk review."
python run_forward_evidence_export.py \
  --db mil3_market.sqlite \
  --trial-id <trial_id> \
  --output evidence/<trial_id>.json
python run_forward_evidence_verify.py \
  --bundle evidence/<trial_id>.json \
  --report evidence/<trial_id>.verification.json
python run_forward_evidence_retain.py \
  --bundle evidence/<trial_id>.json \
  --archive-dir /Volumes/AARS-Evidence/forward
python run_isolated_activation_review.py \
  --db mil3_market.sqlite \
  --trial-id <trial_id> \
  --action REJECT_ISOLATED_PAPER_ACTIVATION \
  --bundle evidence/<trial_id>.json \
  --reviewer local-owner \
  --note "Evidence is not ready."
python run_isolated_paper_config.py \
  --db mil3_market.sqlite \
  --action REGISTER \
  --trial-id <trial_id>
python run_isolated_paper_config.py \
  --db mil3_market.sqlite \
  --action ACTIVATE \
  --configuration-id <configuration_id> \
  --sandbox-id aars-paper-sandbox \
  --operator local-owner \
  --note "Select isolated registry pointer."
python run_isolated_paper_config.py \
  --db mil3_market.sqlite \
  --action RECONCILE
python run_isolated_paper_runtime.py \
  --db mil3_market.sqlite \
  --action CLEAR_KILL \
  --sandbox-id aars-paper-sandbox \
  --operator local-owner \
  --note "Initialize governed runtime control."
python run_isolated_paper_runtime.py \
  --db mil3_market.sqlite \
  --action RUN \
  --sandbox-id aars-paper-sandbox \
  --max-cycles 1
python run_isolated_paper_runtime.py \
  --db mil3_market.sqlite \
  --action RECONCILE
python run_forward_bot_operations.py \
  --db mil3_market.sqlite \
  --action STATUS \
  --sandbox-id aars-paper-sandbox
python run_strategy_diagnostics.py \
  --db mil3_market.sqlite \
  --output-json reports/mil327-diagnostic.json
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
- MIL-3.17 deterministic tests cover strict forward boundaries, synchronized assets, warmup exclusion, dynamic funding completeness, eligible-trial enforcement, hard stops, immutable lineage, read-only API/CLI authority and UI boundary visibility.
- MIL-3.18 deterministic tests cover minimum horizon and confirmation streaks, decay/reversal/rising-risk alarms, hard-stop precedence, lineage/cadence deferral, bounded monitoring, idempotent endpoint reuse, waiting states, read-only stability API/CLI authority and UI alarm actionability.
- MIL-3.19 deterministic tests cover lifecycle transitions, irreversible termination, stale/tampered review rejection, monitor holds, deterministic self-verifying non-overwriting exports, read-only APIs, explicit local CLIs and UI authority gates.
- MIL-3.20 deterministic tests cover strict offline verification, duplicate keys, safe retention and pruning, minimum-copy floors, approval prerequisites, expiry/revocation, stale/tampered evidence, read-only APIs, explicit local CLIs and UI action gates.
- MIL-3.21 deterministic tests cover unique approval consumption, inert registration, optimistic races, monotonic events, atomic activation/rollback, immediate expiry/revocation suppression, reconciliation, read-only APIs, explicit local CLIs and UI stored/effective separation.
- MIL-3.22 deterministic tests cover fail-safe kill-switch initialization, fenced lease acquisition, token rejection, heartbeat renewal, lease timeout, pointer-version fencing, atomic takeover, kill-switch stop, bounded completion, read-only APIs, explicit local CLI and UI stored/effective runtime separation.
- MIL-3.23 deterministic tests cover synchronized content-addressed snapshots, cumulative paper ledgers, atomic reserve/commit, duplicate reuse, crash recovery, stale-owner fencing, source drift, result tampering, monotonic checkpoint chains, read-only APIs, bounded CLI and UI commit/recovery evidence.
- MIL-3.24 deterministic tests cover four-bot isolation, common snapshot/configuration binding, stable account identity, parameterized 10x Futures Grid, simulated fill evidence, flatten-and-freeze risk stops, fleet/result tamper detection, duplicate reuse, read-only API and no-control UI visibility.
- MIL-3.25 deterministic tests cover complete-candle gating, duplicate/still-open waits, next-boundary execution, cycle/account deltas, concurrent wake fencing, stale RESERVED alerts, 7/14-day continuity and reset, explicit CLI, deferred one-shot LaunchAgent generation, read-only API and no-control UI evidence.
- MIL-3.26 deterministic tests cover synchronized closed-boundary selection, open-candle mutation immunity, canonical UTC-day uniqueness, idempotent reruns, legacy audit retention, v2-only promotion eligibility and archived-versus-eligible governance counts.
- MIL-3.27 deterministic tests cover immutable-v2 replay reconciliation, asset/baseline/cost/direction/regime attribution, accounting add-back limitations, tamper/degraded behavior, GET-only API authority and task-centered HMI gates.

## Definition of Done

MIL-3 is complete when AARS can ingest current BTC/ETH/SOL data, classify state with evidence, produce calibrated probability outputs, execute only in a paper ledger, replay historical periods, compare strategies and expose the result through an auditable API/UI without any live-order capability.
