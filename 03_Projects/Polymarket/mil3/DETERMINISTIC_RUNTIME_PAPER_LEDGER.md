# MIL-3.23 Deterministic Runtime Paper Ledger

MIL-3.23 turns each valid MIL-3.22 heartbeat into at most one deterministic,
content-addressed paper-ledger calculation. It reads normalized public market
data from SQLite and never creates an external order request.

## Cycle contract

```text
effective fenced runtime lease
  -> synchronized stored-candle boundary
  -> immutable input hashes
  -> RESERVED checkpoint
  -> deterministic ReplayEngine paper calculation
  -> source revalidation under write lock
  -> ledger result + COMMITTED checkpoint in one transaction
```

The cycle ID is derived from sandbox ID, configuration ID and synchronized
snapshot boundary. It deliberately excludes session ID: a replacement fenced
session can recover the same RESERVED cycle after a crash without calculating a
second logical cycle.

## Read-only market snapshot

The snapshot uses only locally stored:

- normalized candles at or before cycle time;
- funding history within the configured replay interval;
- observed funding-cadence history, including the preceding cadence record.

All configured assets use the latest common candle boundary. Each asset records
its evidence start, replay start, boundary, row counts, funding coverage and
input SHA-256. The combined snapshot also binds configuration SHA-256, symbols,
timeframe, replay window and warmup.

No ingestion or market row is changed by the runtime cycle.

Beginning with MIL-3.25, the boundary must also identify a fully closed candle:
`open_time + timeframe_duration <= cycle_time`. Stored still-open rows are
ignored, and an explicitly supplied still-open recovery boundary is rejected.

## Deterministic paper ledger

The calculation reuses the existing unified `ReplayEngine`, configured proposed
strategy and paper settings. It produces cumulative per-asset ledger summaries
through the snapshot boundary plus portfolio-level aggregation:

- initial/final equity and return;
- realized P&L and realized grid P&L;
- inventory unrealized P&L;
- fees, slippage and funding;
- turnover and exposure;
- effective leverage, margin buffer and liquidation-risk approximation.

The result ID excludes wall-clock completion time and binds the deterministic
strategy, snapshot, configuration and ledger output. Result payloads remain
strict finite JSON.

MIL-3.24 ledger v2 additionally embeds a separately hashed four-bot fleet for
Buy & Hold, Spot Grid, Futures Long Grid and AARS Dynamic. All accounts share
the exact snapshot but remain capital/accounting isolated. Complete funding
coverage is now mandatory for the fleet because two fixed bots use funding.
Legacy committed ledger v1 results remain verifiable and read-only.

## Atomic checkpoint and idempotency

Checkpoint states are:

- `RESERVED` — snapshot is fixed but no ledger result is effective;
- `COMMITTED` — result insertion and checkpoint transition succeeded together.

SQLite uniqueness constraints enforce one logical cycle per sandbox,
configuration and boundary, one result per cycle and one event per checkpoint
version. A repeated cycle at the same boundary returns `REUSED_COMMITTED` and
does not insert or apply another result.

Committed cycles form a monotonic chain using `previous_committed_cycle_id`.
Every result is cumulative, so recovery never depends on partially mutated
in-memory portfolio state.

## Crash recovery

If the process stops after `RESERVE` but before `COMMIT`, the checkpoint remains
RESERVED. A new session may claim it only after the previous owner is no longer
effectively RUNNING. Recovery increments attempt/version and appends `RECOVER`.

Before commit, the runtime rebuilds the exact reserved snapshot while holding a
write lock. Changed candles, funding, cadence, configuration, pointer, lease,
token or kill-switch authority blocks commit. Result and checkpoint changes
then commit atomically; an exception leaves both absent.

## Local operation

MIL-3.22's bounded RUN command now performs these calculations:

```bash
python run_isolated_paper_runtime.py \
  --db mil3_market.sqlite \
  --action RUN \
  --sandbox-id aars-paper-sandbox \
  --worker-id aars-local-paper-worker \
  --lease-seconds 120 \
  --heartbeat-interval-seconds 30 \
  --max-cycles 1
```

Insufficient synchronized history returns `WAITING`. Funding gaps, source drift
or authority failures return `BLOCKED`; they never infer a committed result.

## Read-only API

```text
GET /api/v1/isolated-runtime-cycles?sandbox_id={sandbox_id}
GET /api/v1/isolated-runtime-cycles/{cycle_id}
GET /api/v1/isolated-runtime-cycle-events?cycle_id={cycle_id}
GET /api/v1/isolated-paper-ledger-results/{result_id}
```

The console exposes checkpoint state, attempts, owner session, prior committed
cycle, snapshot hashes/boundary, ledger attribution and the immutable
reserve/recover/commit trail. It has no run, recover or commit control.

## Permanent safety boundary

```text
execution_mode=PAPER_ONLY
market_source_read_only=true
external_order_requests_created=false
order_path_present=false
shared_configuration_change_allowed=false
automatic_strategy_change_allowed=false
live_execution_allowed=false
```
