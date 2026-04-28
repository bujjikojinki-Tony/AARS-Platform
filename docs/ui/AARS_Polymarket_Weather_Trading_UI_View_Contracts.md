# AARS Polymarket Weather Trading Console
# UI View Contracts

版本：v1.0  
日期：2026-04-25

## Contract Table

| Page | Primary Contract | Summary Contract |
|---|---|---|
| Operations Monitor | `operations_monitor_view.v1` | `operations_monitor_summary.v1` |
| Monitoring Signals | `monitoring_signals_view.v1` | `monitoring_signals_summary.v1` |
| Opportunity Board | `opportunity_board_view.v1` | `opportunity_board_summary.v1` |
| Workstation | `market_workstation_view.v1` | `market_workstation_summary.v1` |
| Command | `command_context_view.v1` | `command_context_summary.v1` |
| Pipeline | `pipeline_status_view.v1` | `pipeline_status_summary.v1` |
| Markets | `markets_inventory_view.v1` | `markets_inventory_summary.v1` |
| Charts | `charts_analysis_view.v1` | `charts_analysis_summary.v1` |
| History | `history_event_view.v1` | `history_event_summary.v1` |
| Evidence / Raw | `evidence_raw_view.v1` | `evidence_raw_summary.v1` |
| Alerts & Rules | `alerts_rules_settings_view.v1` | `alerts_rules_settings_summary.v1` |
| Data & Sources | `data_sources_settings_view.v1` | `data_sources_settings_summary.v1` |
| System | `system_settings_view.v1` | `system_settings_summary.v1` |

## Cross-Page Action Event Contract

```json
{
  "schema_version": "ui_action_event.v1",
  "created_at": "2026-04-26T13:10:00Z",
  "page": "workstation",
  "action": "review_evidence",
  "market_id": "mkt_ny_rain_50mm",
  "detail": {
    "source": "workstation",
    "note": "operator requested raw evidence review"
  },
  "source_page": "workstation",
  "target_page": "evidence_raw",
  "entry_context": {}
}
```

This event contract is used for dashboard-local UI action audit, History replay, and future summary alignment across Dashboard / Telegram / CLI.

## Common Market State Fields

```json
{
  "market_id": "mkt_ny_rain_50mm",
  "primary_state": "BLOCKED",
  "primary_state_reason": "Gate blocked by validation coverage below threshold",
  "secondary_states": ["LIVE", "DATA_QUALITY_B"],
  "display_priority": 92,
  "next_operator_action": "review_evidence",
  "gate_summary": {
    "can_execute": false,
    "primary_block_reason": "validation coverage < 80%"
  },
  "upstream_refs": {},
  "policy_refs": {}
}
```

## Command Context View

```json
{
  "schema_version": "command_context_view.v1",
  "selected_market_id": "new_york_rainfall_50mm",
  "entry_source": "operations_monitor_focus",
  "primary_state": "BLOCKED",
  "next_operator_action": "review_evidence",
  "gate_stack_summary": {},
  "operator_decision_panel": {},
  "authorization_gateway_panel": {},
  "audit_trail": [],
  "available_actions": [],
  "disabled_actions": []
}
```

## Surface Consistency

Dashboard, Telegram, CLI, and reports must consume the same contract family.

```text
Dashboard /monitor  -> operations_monitor_view.v1
Telegram /monitor   -> operations_monitor_summary.v1
Dashboard /command  -> command_context_view.v1
Telegram /command   -> command_context_summary.v1
```

## Settings Contract Additions

### Alerts & Rules

```json
{
  "schema_version": "alerts_rules_settings_view.v1",
  "generated_at": "2026-04-24T14:32:18Z",
  "summary": {
    "total_rules": 48,
    "active_rules": 34,
    "disabled_rules": 8,
    "testing_rules": 6
  },
  "rules": [],
  "selected_rule_detail": {},
  "policy_refs": {}
}
```

### Data & Sources

```json
{
  "schema_version": "data_sources_settings_view.v1",
  "generated_at": "2026-04-24T14:32:18Z",
  "summary": {
    "total_sources": 26,
    "active_sources": 22,
    "degraded_sources": 2,
    "down_sources": 2,
    "avg_freshness_minutes": 18,
    "avg_precision_score": 0.87,
    "market_coverage": 0.92
  },
  "sources": [],
  "selected_source_detail": {},
  "policy_refs": {}
}
```

### System

```json
{
  "schema_version": "system_settings_view.v1",
  "generated_at": "2026-04-24T14:32:18Z",
  "summary": {
    "overall_status": "healthy",
    "cpu_usage": 0.24,
    "memory_usage": 0.61,
    "disk_usage": 0.48,
    "services_running": 36,
    "services_total": 36,
    "errors_24h": 3,
    "alerts_24h": 14
  },
  "service_status": [],
  "system_metrics": {},
  "recent_events": [],
  "system_information": {},
  "available_actions": []
}
```

## Contract Maturity Notes

- `operations_monitor_view.v1`: backed by current view builder output and now has a stricter schema draft.
- `opportunity_board_view.v1`: backed by current opportunity board writer output and now has a stricter schema draft.
- `market_workstation_view.v1`: backed by current workstation builder output and now has a stricter schema draft.
- `command_context_view.v1`: currently serves as the governed target contract for the Command page and is not yet backed by a dedicated comparison-engine command view builder.
- `alerts_rules_settings_view.v1`, `data_sources_settings_view.v1`, and `system_settings_view.v1`: governed target contracts for the Settings family and should remain registry-first rather than frontend-derived.
