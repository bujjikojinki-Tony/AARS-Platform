# AARS Polymarket Weather Trading Console
# UI Surface Consistency

版本：v1.0  
日期：2026-04-25

## Purpose

Dashboard, Telegram, CLI, and reports must show consistent state and action meaning for the same market and event context.

## Surface Mapping

| Surface | Route / Command | Contract |
|---|---|---|
| Dashboard | `/monitor` | `operations_monitor_view.v1` |
| Telegram | `/monitor` | `operations_monitor_summary.v1` |
| Dashboard | `/signals` | `monitoring_signals_view.v1` |
| Telegram | `/signals` | `monitoring_signals_summary.v1` |
| Dashboard | `/opportunities` | `opportunity_board_view.v1` |
| Telegram | `/opportunities` | `opportunity_board_summary.v1` |
| Dashboard | `/command` | `command_context_view.v1` |
| Telegram | `/command` | `command_context_summary.v1` |
| Dashboard | `/history` | `history_event_view.v1` |
| Telegram | `/history` | `history_event_summary.v1` |

## Consistency Rules

- Telegram must not independently compute `primary_state`.
- CLI must not independently compute gate permission.
- Reports must not reinterpret `ALERT`, `ANOM`, or `BLOCKED`.
- If a summary contract omits detail, it must still preserve state, next action, gate boundary, and refs.

## Acceptance

- Dashboard and Telegram show consistent `primary_state`, `gate_summary`, and `next_operator_action`.
- Action events are written to a shared audit trail.
- No surface derives execution permission from opportunity or anomaly signals.

