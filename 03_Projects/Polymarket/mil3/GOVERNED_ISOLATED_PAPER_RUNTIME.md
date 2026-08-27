# MIL-3.22 Governed Isolated PAPER_ONLY Runtime

MIL-3.22 adds a local runtime authority layer after the MIL-3.21 registry. It
consumes only the registry's current `effective_configuration`; it does not
start historical replay, connect to an exchange or expose an order path.

## Authority chain

```text
verified evidence
  -> unexpired isolated approval
  -> immutable registered configuration
  -> effective sandbox pointer
  -> explicitly clear kill switch
  -> fenced short runtime lease
  -> token-checked heartbeat
```

Every runtime session is bound to its sandbox ID, configuration ID,
configuration SHA-256 and sandbox state version. A pointer change, expiry,
revocation, configuration mismatch, lost lease or armed kill switch makes the
stored session ineffective immediately.

## Fail-safe kill switch

An uninitialized kill switch is treated as `ARMED`. Clear it explicitly before
the first local run:

```bash
python run_isolated_paper_runtime.py \
  --db mil3_market.sqlite \
  --action CLEAR_KILL \
  --sandbox-id aars-paper-sandbox \
  --operator local-owner \
  --note "Reviewed registry authority for one bounded paper run."
```

Clearing the switch never starts or restarts a session. Arm it to stop every
running session in that sandbox in the same SQLite transaction:

```bash
python run_isolated_paper_runtime.py \
  --db mil3_market.sqlite \
  --action ARM_KILL \
  --sandbox-id aars-paper-sandbox \
  --operator local-owner \
  --note "Immediate local paper-runtime stop."
```

## Bounded runtime

```bash
python run_isolated_paper_runtime.py \
  --db mil3_market.sqlite \
  --action RUN \
  --sandbox-id aars-paper-sandbox \
  --worker-id aars-local-paper-worker \
  --lease-seconds 30 \
  --heartbeat-interval-seconds 10 \
  --max-cycles 6
```

Acquisition returns an opaque fencing token only to the in-process worker. The
database stores its SHA-256, and the read-only API never returns the token.
Each heartbeat renews the lease only after rechecking:

- fencing-token hash;
- current RUNNING session and monotonic heartbeat time;
- clear kill switch;
- lease deadline;
- exact sandbox pointer and state version;
- current approval lineage and expiry;
- immutable configuration hash.

The bounded worker records `START`, `HEARTBEAT` and `STOP` events. A heartbeat
means governed configuration identity was consumed; it does not calculate a
replay, create a paper order or submit a live order. Completion stops the
session rather than leaving a lease behind.

## Derived and persisted stops

Read-only resolution distinguishes `stored_status` from `effective_status`.
Possible fail-safe states include:

- `LEASE_EXPIRED_FAIL_SAFE`;
- `KILL_SWITCH_FAIL_SAFE`;
- `POINTER_CHANGED_FAIL_SAFE`;
- approval expiry, revocation or mismatch fail-safe states;
- `CONFIGURATION_HASH_FAIL_SAFE`.

GET requests never persist a stop. The worker persists a stop when its next
heartbeat detects the condition. An operator may persist already-derived
fail-safe stops with:

```bash
python run_isolated_paper_runtime.py \
  --db mil3_market.sqlite \
  --action RECONCILE
```

Safety does not depend on reconciliation: consumers must honor
`effective_status`, never only the stored RUNNING value.

## Read-only API

```text
GET /api/v1/isolated-runtime?sandbox_id={sandbox_id}
GET /api/v1/isolated-runtime-sessions/{session_id}
GET /api/v1/isolated-runtime-events?session_id={session_id}
GET /api/v1/isolated-runtime-kill-events?sandbox_id={sandbox_id}
```

The browser exposes actual/effective state, heartbeat age, lease deadline,
configuration binding, kill-switch state, immutable histories and recovery
guidance. It contains no run, stop, clear or arm control.

## Permanent exclusions

```text
execution_mode=PAPER_ONLY
replay_started=false
order_path_present=false
shared_configuration_change_allowed=false
automatic_strategy_change_allowed=false
live_execution_allowed=false
```
