# AARS Polymarket Weather Trading Console
# UI Action Policy

版本：v1.0  
日期：2026-04-25

## Principle

Action visibility must be policy-driven. No frontend page may independently decide that an execution-related button is allowed.

Execution-related actions must depend on:

- `action_visibility_policy`
- `gate_stack_api`
- authorization status
- pending intent status
- mode configuration

## Global Action Table

| Action | Allowed Pages | Target / Output | Changes Gate? | Creates Intent? |
|---|---|---|---|---|
| Open Workstation | Monitor, Signals, Board, Command, Markets, History | `market_workstation_view.v1` | No | No |
| Add to Focus | Board, Markets, Workstation, Command | `focus_market_list.v1` | No | No |
| Send to Command | Monitor, Signals, Board, Workstation | `command_context_view.v1` | No | Optional |
| Review Evidence | Signals, Board, Workstation, Command | `evidence_raw_view.v1` | No | No |
| View History | Command, Workstation, Signals, Pipeline | `history_event_view.v1` | No | No |
| Acknowledge Signal | Signals, Command, Monitor detail | `signal_ack_event.v1` | No | No |
| Mute Signal | Signals, Command | `signal_mute_event.v1` | No | No |
| Create Pending Intent | Command only | `pending_intent.v1` | No | Yes |
| Run Dry-run Check | Command, Workstation gate panel | `gateway_dry_run_result.v1` | No | No |
| Live Execute | Command only, future gated mode | Execution client | Yes, must require gate allow | Yes |

## UI Action Audit

All dashboard-local operator actions that affect navigation, review flow, focus state, muting, notes, replay, or evidence access should emit a `ui_action_event.v1` record.

Typical actions include:

- `open_workstation`
- `send_to_command`
- `review_evidence`
- `add_to_focus`
- `mute_signal`
- `save_note`
- `view_gate_detail`
- `open_history`
- `open_replay`

These actions do not change gate semantics by themselves, but they must remain auditable and replayable in `History`.

## Page Constraints

Board / Monitor / Markets may show `View`, `Add to Focus`, `Open Workstation`, and `Send to Command`. They must not expose `Run Dry-run` or `Live Execute` as primary actions.

Workstation may show `Review Evidence`, `Open Charts`, `Send to Command`, and secondary `Run Dry-run Review`. It must not directly live execute.

Command may show `Acknowledge`, `Mute`, `Create Pending Intent`, and `Run Dry-run`. Future `Live Execute` must only appear under strong gate, approval, risk, and mode conditions.

## Settings Action Policy

Settings pages are configuration-first and registry-first. Their actions must not bypass Pipeline, Command, or Gate.

### Alerts & Rules

| Action | Output Object | Notes |
|---|---|---|
| New Rule | `alert_rule_draft.v1` | Must default to `testing` or `disabled` |
| Test Rule | `alert_rule_test_result.v1` | Must not send real notifications |
| Enable / Disable | `alert_rule_update_event.v1` | Must write audit trail |
| Import / Export | config file | Must validate schema before apply |
| Delete | `alert_rule_deprecated_event.v1` | Prefer soft delete |

### Data & Sources

| Action | Output Object | Notes |
|---|---|---|
| Add Source | `data_source_contract_draft.v1` | New sources should default to testing |
| Test Connection | `source_connection_test_result.v1` | Must not alter production routing |
| Enable / Disable | `source_status_update_event.v1` | High-risk changes require confirmation |
| Edit Mapping | `measurement_mapping_update_event.v1` | Must be versioned |
| Refresh Now | `source_refresh_request.v1` | Must write audit trail |

### System

| Action | Output Object | Notes |
|---|---|---|
| Restart Services | `system_maintenance_event.v1` | Requires permission and confirmation |
| Clear Cache | `system_maintenance_event.v1` | Must write audit trail |
| Run Diagnostics | `system_diagnostics_result.v1` | Must be replayable in History |
| Download Logs | log export | Must not alter runtime state |
| Change Config | `system_config_update_event.v1` | Must be versioned |

## Settings Guardrails

- Critical rule, source, and system changes should require secondary confirmation.
- Settings actions must write to audit trail / History.
- Settings actions must update registries or policies rather than scattered files.
- Settings pages may influence runtime behavior only through registries, policy loaders, adapters, or view builders.
- Settings pages must not directly grant execution permission or rewrite market gate semantics.
