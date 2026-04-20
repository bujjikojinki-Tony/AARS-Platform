# weather-execution-gateway

Guarded execution gateway for weather-market strategies.

## Operating Modes

The safest default operating mode is `manual_advisory`.

In this mode:
- BOT can notify the operator with market context, model evidence, suggested side, price and size.
- The operator places any order manually on the exchange.
- No account connector, private key, or CLOB order submission is required.
- Telegram approval means operator review/acknowledgement, not autonomous execution.

This mode is intentionally different from live execution. Live execution remains blocked unless every production-readiness gate passes.

Manual advisory actions are audit-friendly:
- Dashboard signal creation appends a `manual_advisory_signal_created` event.
- Telegram operator acknowledgement appends an `operator_acknowledged_manual_advisory` event.
- Human-reported fills append `human_fill_reported` plus a fill record.

## Purpose

This repository receives approved order intents and decides whether they are allowed to proceed.

It does:
- apply risk gates
- enforce market whitelist
- enforce kill switch
- produce execution results
- persist audit events
- support dry-run mode
- define a disabled-by-default CLOB adapter contract for future live execution

It does not:
- generate signals
- manage Telegram UX
- run autonomous strategies by default

## Default Safety Posture

Execution is disabled by default.
Dry-run mode is the default mode.
The production-readiness checker can report whether live execution would be allowed, but it never enables live trading by itself.

## Inputs

Expected upstream inputs:
- signal-driven order intents
- market whitelist
- risk limits
- execution mode flags

## Outputs

Primary outputs:
- ExecutionResult
- RiskState
- AuditEvent
- ProductionReadinessReport

## Production Readiness Check

Generate the pre-flight report used by the dashboard live gate:

```bash
PYTHONPATH=src python -m weather_execution_gateway.main check-production-readiness
```

The report is written to:

```text
data/outputs/production_readiness_report.json
```

The default repository config is intentionally blocked for live execution. A blocked report means the gateway must remain disabled / dry-run even if an operator approval exists.

The checker also probes the Telegram approval database when available. An expired or missing active approval is reported as an operator-channel warning; individual orders still require a fresh approval before execution.

## CLOB Adapter Stub

The Polymarket CLOB execution contract lives in:

```text
src/weather_execution_gateway/polymarket/clob_execution.py
```

The default adapter is `DisabledClobExecutionAdapter`, which always rejects submissions with `clob_adapter_disabled`. This is intentional: it lets the gateway test live-order plumbing without private keys or accidental real orders.

Adapter readiness is controlled by:

```text
config/clob_adapter.yaml
```

The default config is disabled and not live-ready.

## Live-Mode Policy

Live execution also requires an explicit policy file:

```text
config/live_mode_policy.yaml
```

The default policy is disabled. To become live-ready, the policy must be enabled, explicitly allow live execution, include enough approvers, define a future expiration timestamp, and keep all required safety checks enabled. This prevents a single config toggle from accidentally enabling live trading.

## Position Exposure Snapshot

Dry-run risk checks now read current exposure from:

```text
data/outputs/position_snapshot.json
```

The snapshot uses:

- `positions` rows with `market_id` plus either explicit `notional` or `size` and `current_price` / `avg_price`
- `open_orders` rows with `market_id` plus either explicit `notional` or `remaining_size` / `remainingSize` and `price`
- `balance` fields with `available_balance`, `total_balance`, `currency`, and `manual_order_only`

The gateway computes per-market and total notional before evaluating exposure limits, so a new intent can be blocked when existing holdings or unfilled orders are already close to the configured limit.

Build or refresh the snapshot from a read-only local account positions file:

```bash
PYTHONPATH=src python -m weather_execution_gateway.main build-position-snapshot
```

By default this reads:

```text
data/outputs/sample_account_positions.json
```

Override with `POSITION_SOURCE_JSON` or pass a source path argument. This producer does not use private keys and does not submit orders.

## Human Fill Feedback

When the system runs without a connected trading account, an operator can report a manually placed order back into the audit trail:

```bash
PYTHONPATH=src python -m weather_execution_gateway.main record-human-fill \
  intent_1 market_1 buy 0.61 10 \
  --signal-id sig_1 \
  --operator-user-id 123 \
  --notes "manual order placed by operator"
```

This command never submits an order. It writes:

```text
data/outputs/human_fills.jsonl
data/outputs/manual_advisory_audit.jsonl
```

Use this as the feedback bridge for manual trading: BOT suggests, human executes externally, and the gateway records the reported fill for later exposure reconciliation and model validation.

Reconcile reported fills against the latest position snapshot:

```bash
PYTHONPATH=src python -m weather_execution_gateway.main reconcile-human-fills
```

The report is written to:

```text
data/outputs/human_fill_reconciliation_report.json
```

Typical statuses:

- `reconciled`: the fill market is visible in position/open-order snapshot and notional is covered.
- `unmatched`: the reported fill market is not visible in the latest snapshot.
- `needs_review`: the market is visible, but notional coverage or price tolerance needs review.

## Operator Dashboard

The Streamlit dashboard reads `data/outputs/production_readiness_report.json` and presents the live gate as an operator checklist grouped by:

- Blocked
- Warnings
- Passed

This is intentionally more explicit than a single status flag. Operators should be able to see exactly why live execution is unavailable before touching any BOT authorization control.

## First MVP

- validate one `OrderIntent`
- enforce whitelist + kill switch + exposure limits
- produce dry-run execution result
- write audit log

## Non-Goals

- no automatic live trading
- no autonomous position management
- no private key handling in MVP
