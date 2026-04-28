# UI Design Status Roadmap

This short-form file is the docs/ui landing version. The full historical roadmap remains at:

`/AARS_Polymarket_Weather_Trading_UI_Design_Status_Roadmap.md`

## Current Page Family

```text
RUN: Operations Monitor, Monitoring Signals, Command
RESEARCH: Opportunity Board, Workstation, Charts
DATA: Pipeline, Markets, Evidence / Raw, History
SETTINGS: Alerts & Rules, Data & Sources, System
```

## Current Boundary Decisions

- Operations Monitor is the default runtime HMI page.
- Opportunity Board is a ranked research candidate board, not a realtime monitor.
- Workstation is the single-market evidence analysis page.
- Command is the operator decision and authorization closure page.
- Pipeline is the data-processing diagnostics page.
- Evidence / Raw is an audit and developer evidence page, not a primary operator decision surface.
- Alerts & Rules is the alert-rule and notification-routing governance page, not a live signal feed.
- Data & Sources is the source-contract, measurement-policy, refresh, and data-quality governance page, not a raw evidence detail page.
- System is the system health, service, maintenance, and admin configuration page, not a market monitoring or trading decision page.

## Settings Design Baseline

The `SETTINGS` group is a governance and configuration backend for runtime pages.

- `Alerts & Rules` supports Monitoring Signals, Operations Monitor, and Command by managing alert rule definitions, routing channels, throttle / suppression logic, and rule testability.
- `Data & Sources` supports Pipeline, Evidence / Raw, Workstation, and Opportunity Board by managing source contracts, measurement mappings, refresh schedules, freshness, precision, and coverage governance.
- `System` supports the full console by exposing service health, runtime diagnostics, maintenance actions, user / permission state, and admin-level system configuration.

These pages may display status summaries, but they must remain configuration-first rather than runtime-first.

## UI Phase Roadmap

- Phase 32: Operations Monitor v3.1 UI Refactor.
- Phase 33: Navigation & Page Contract Alignment.
- Phase 34: Legend & Dynamic Parameter Governance.
- Phase 35: Surface Consistency: Dashboard / Telegram / CLI.
- Phase 36: Settings Governance Pages.
