# MIL-3.25 Forward Bot Operations

MIL-3.25 operates the four MIL-3.24 shadow bots on newly available synchronized,
fully closed candles. It is a local PAPER_ONLY scheduler and evidence surface;
it does not ingest market data, hold exchange credentials or create external
orders.

## Closed-candle trigger

For timeframe `T`, a candle is eligible only when:

```text
candle.open_time + duration(T) <= evaluated_at
```

The trigger finds the latest eligible candle per configured asset and selects
their minimum as the synchronized boundary. A wake runs only when that boundary
is later than the latest committed cycle. A stored still-open candle is ignored.

Repeated wakes at the same boundary return `WAITING_NO_NEW_CLOSED_BAR`. If two
wakes race, the existing sandbox runtime lease permits one active worker and the
second returns `SKIPPED_CONCURRENT_WAKE`. Cycle/checkpoint uniqueness remains
the final idempotency authority.

## One bounded wake

```bash
python run_forward_bot_operations.py \
  --db mil3_market.sqlite \
  --action WAKE \
  --sandbox-id aars-paper-sandbox \
  --lease-seconds 120
```

Read current operations evidence without acquiring a lease:

```bash
python run_forward_bot_operations.py \
  --db mil3_market.sqlite \
  --action STATUS \
  --sandbox-id aars-paper-sandbox
```

A foreground scheduler is available for supervised burn-in:

```bash
python run_forward_bot_operations.py \
  --db mil3_market.sqlite \
  --action FOREGROUND \
  --poll-seconds 60 \
  --max-wakes 0
```

Ingestion remains the separate `run_scheduler.py` process. The forward runner
only reads normalized local market rows and writes governed runtime/checkpoint/
paper-ledger evidence.

## Cycle-to-cycle account delta

Every operations view compares the latest two verified ledger v2 results for
each stable bot account ID. It reports changes in:

- equity and total return;
- realized, grid and inventory unrealized P&L;
- fees, slippage and funding;
- position, exposure, leverage, margin and liquidation risk;
- new deterministic simulated fills per asset.

The first committed result is labeled `GENESIS`; no prior value is inferred.
Legacy or hash-invalid ledgers produce `UNAVAILABLE`, not a fabricated delta.

## Actionable alerts

The content-addressed read-only operations report derives alerts from immutable
registry, kill-switch, market snapshot, checkpoint and ledger evidence:

- `CONFIGURATION_NOT_EFFECTIVE`;
- `KILL_SWITCH_ARMED`;
- `CLOSED_CANDLE_MISSING` / `CLOSED_CANDLE_STALE`;
- `CHECKPOINT_RESERVED_TOO_LONG`;
- `COMMITTED_RESULT_MISSING` / `LEDGER_INTEGRITY_FAILED`;
- `FUNDING_COVERAGE_GAP`;
- `BOT_RISK_FROZEN`;
- `NEW_CLOSED_BAR_PENDING`;
- `BURN_IN_INCOMPLETE`.

Every alert contains severity, affected object, trigger, impact and recommended
response. Alerts do not clear a kill switch, recover a checkpoint or change a
configuration.

## 7–14 day burn-in

Burn-in uses the continuous suffix of committed closed-bar boundaries. A gap
larger than two configured intervals resets the suffix window.

- `< 7 days`: `BURN_IN_RUNNING`;
- `>= 7 days`: `MINIMUM_7D_REACHED`;
- `>= 14 days`: `TARGET_14D_REACHED`.

The report includes continuous cycle count, observed days, 7-day/14-day
progress, maximum observed gap and exact first/latest boundaries. Reaching a
duration does not authorize strategy promotion or live execution.

## Read-only API and console

```text
GET /api/v1/forward-bot-operations?sandbox_id={sandbox_id}
```

The console shows closed-bar trigger state, current-vs-prior bot deltas, burn-in
progress and actionable alerts. It provides no WAKE, RUN, STOP, RECOVER,
kill-switch or order control.

## Deferred Mac mini scheduling

The default Mac install remains unchanged and does not include forward bots.
Generate a separate one-shot LaunchAgent artifact for later review:

```bash
python run_macos_service.py render-forward-bots \
  --runtime-root "$HOME/AARS-MIL3" \
  --agents-dir "$HOME/AARS-MIL3/staged-launch-agents" \
  --sandbox-id aars-paper-sandbox \
  --forward-poll-seconds 60 \
  --forward-lease-seconds 120
```

The generated job has `RunAtLoad=false`, `KeepAlive=false` and invokes one WAKE
per `StartInterval`. Rendering does not load it. Installation/activation remains
deferred until the Mac mini, database, backups, kill-switch procedure and
notification path are reviewed.

## Permanent safety boundary

```text
execution_mode=PAPER_ONLY
closed_candles_only=true
bounded_lease_only=true
public_market_ingestion_started=false
external_order_requests_created=false
order_path_present=false
automatic_strategy_change_allowed=false
live_execution_allowed=false
```
