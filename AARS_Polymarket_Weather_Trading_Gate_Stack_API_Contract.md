# AARS Polymarket Weather Trading - Gate Stack API Contract

## 1. Purpose

`gate_stack_api.v1` is the external stable contract for cross-surface gating semantics.

It is designed for:
- Dashboard compact gate stack consumption
- Telegram `/status` and market-level operator status consumption
- Gateway pre-execution fallback consumption
- Automation consumers that need deterministic `can_execute` + action hints

This contract prevents each surface from re-deriving inconsistent gate logic.

---

## 2. File Outputs

Primary outputs:

- `weather-comparison-engine/data/outputs/gate_stack_api.json`
- `weather-comparison-engine/data/outputs/gate_stack_automation_summary.json`
- `weather-comparison-engine/data/outputs/gate_stack_ops_alerts.jsonl`

Generation commands:

```bash
cd /Users/maolei/AARS-Platform/weather-comparison-engine
PYTHONPATH=src python -m weather_comparison_engine.main build-unified-status
PYTHONPATH=src python -m weather_comparison_engine.main build-gate-stack-api
PYTHONPATH=src python -m weather_comparison_engine.main build-gate-stack-automation-summary
PYTHONPATH=src python -m weather_comparison_engine.main run-gate-stack-automation-check --fail-on-signal red
PYTHONPATH=src python scripts/run_gate_stack_automation_realtime.py
```

---

## 3. `gate_stack_api.v1` Schema

Top-level fields:

- `schema_version`: `gate_stack_api.v1`
- `generated_at`
- `source_schema_version` (expected: `unified_status.v1`)
- `overall_status`
- `market_id` (current market)
- `gate_stack` (global/current-market gate view)
- `block_reasons`
- `can_execute`
- `primary_block_reason`
- `severity`
- `recommended_operator_action`
- `market_count`
- `market_gate_views[]` (multi-market contract views)

`gate_stack` / `market_gate_views[*]` gate fields:

- `data_gate`
- `resolver_gate`
- `probability_gate`
- `freshness_gate`
- `authorization_gate`
- `execution_gate`
- `<gate>_reasons`
- `block_reasons`

Automation hints:

- `severity`: `low | medium | high`
- `recommended_operator_action`:
  - `allow_live_execution`
  - `manual_advisory_only`
  - `review_resolver_contract`
  - `refresh_pipeline_inputs`
  - `check_gateway_readiness`
  - `hold_execution_and_review`

---

## 4. Consumption Rules

### Dashboard

- Prefer `unified_status.gate_stack` when market matches.
- Else prefer `gate_stack_api.market_gate_views` by selected `market_id`.
- Else fallback to `gate_stack_api.gate_stack`.
- Else fallback to local-derived gate stack.

### Telegram `/status`

- If unified status exists, merge `gate_stack_api` (market-specific view first).
- If unified status missing, build status payload directly from `gate_stack_api`.

### Gateway

- If unified status missing or lacks gate stack, fallback to `gate_stack_api`.
- Fallback must match `intent.market_id` to `market_gate_views`.

---

## 5. Versioning Strategy

Versioning policy is additive-first:

1. `v1.x` minor updates: additive fields only; existing fields keep semantics.
2. Breaking semantic changes require new major contract version (`gate_stack_api.v2`).
3. Consumers should:
   - validate `schema_version` explicitly
   - ignore unknown fields
   - preserve blocker semantics for existing gate keys

Compatibility guarantees for `v1`:

- Required gate keys remain stable.
- `can_execute` remains derived from authorization + execution gate pass state.
- `primary_block_reason` is deterministic first blocker in merged reason set.

---

## 6. Automation Summary Contract

`gate_stack_automation_summary.v1` is a simplified automation-facing derivative with:

- `can_execute`
- `severity`
- `recommended_operator_action`
- `primary_block_reason`
- compact gate states
- `automation_signal` (`green | amber | red`)

Use this output for cron/heartbeat automation routing and notifications.

---

## 7. Ops Alert Bridge

When runtime check exits non-zero and `automation_signal=red`, the system appends:

- `gate_stack_ops_alert.v1` JSONL event to `gate_stack_ops_alerts.jsonl`

Core fields:

- `severity`
- `automation_signal`
- `exit_code`
- `fail_on_signal`
- `market_id`
- `primary_block_reason`
- `recommended_operator_action`
- `block_reasons`

This is the bridge artifact for Telegram/ops notification integration.

Upstream monitoring indicator events such as `market_alert_event.v1` and `market_anomaly_event.v1` are separate contracts. They may feed dashboard / telegram / automation consumers, but they do not redefine `gate_stack_api.v1` semantics.

Telegram bridge queue layer:

- bridge command: `weather-telegram-ops-bridge sync-gate-alerts --max-batch 50`
- input: `gate_stack_ops_alerts.jsonl`
- outputs:
  - `telegram_ops_notifications.jsonl` (`telegram_ops_notification.v1`)
  - `ops_alert_bridge_state.json` (dedupe cursor/state)
  - `telegram_ops_delivery_log.jsonl` (dispatch/ack delivery events)

Queue lifecycle commands:

- `weather-telegram-ops-bridge dispatch-ops-queue --max-batch 20` (`pending -> sent`)
- `weather-telegram-ops-bridge ack-ops --notification-id <id> --acked-by <user>` (`sent -> acked`)
